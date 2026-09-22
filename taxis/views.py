from datetime import timedelta
from decimal import Decimal
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from functools import wraps

from django.contrib.staticfiles import finders
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.functional import cached_property
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, FormView

from taxis import services
from taxis.forms import (
    DirectRequestForm,
    DriverProfileForm,
    DriverSignupForm,
    GoingToForm,
    PaymentProofForm,
    RequestTaxiForm,
    ReviewForm,
)
from taxis.models import (
    CarType, Driver, FAQ, Fare, GoingToPost, Lead, Payment, PushSubscription, TabEntry,
)
from taxis.services import Unlock
from taxis.utils.emails import send_welcome_email
from taxis.utils.whatsapp import build_wa_link, hail_message, share_profile_message


def home(request):
    drivers = Driver.objects.filter(is_active_listing=True).select_related("user")

    destination = request.GET.get("destination", "").strip()
    car_type = request.GET.get("car_type", "").strip()
    min_seats = request.GET.get("seats", "").strip()
    online_only = request.GET.get("online_only") == "1"

    if destination:
        drivers = drivers.filter(routes__icontains=destination)
    if car_type:
        drivers = drivers.filter(car_type=car_type)
    if min_seats.isdigit():
        drivers = drivers.filter(seats__gte=int(min_seats))

    drivers = list(drivers)
    if online_only:
        drivers = [d for d in drivers if d.is_online]

    # Pro/verified first (model default ordering), online drivers bubbled up next.
    drivers.sort(key=lambda d: (not d.is_online,))

    going_to_posts = GoingToPost.objects.filter(
        expires_at__gt=timezone.now()
    ).select_related("driver")[:10]

    context = {
        "drivers": drivers,
        "going_to_posts": going_to_posts,
        "car_types": CarType.choices,
        "filters": {
            "destination": destination,
            "car_type": car_type,
            "seats": min_seats,
            "online_only": online_only,
        },
    }
    return render(request, "taxis/home.html", context)


def fares(request):
    fare_list = Fare.objects.all()
    return render(request, "taxis/fares.html", {"fares": fare_list})


def driver_profile(request, slug):
    driver = get_object_or_404(Driver, slug=slug, is_active_listing=True)
    review_form = ReviewForm()

    if request.method == "POST" and "submit_review" in request.POST:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.driver = driver
            review.save()
            messages.success(request, "Thanks for the review.")
            return redirect("taxis:driver_profile", slug=driver.slug)

    profile_url = request.build_absolute_uri(
        reverse("taxis:driver_profile", args=[driver.slug])
    )
    context = {
        "driver": driver,
        "review_form": review_form,
        "share_text": share_profile_message(profile_url),
        "profile_url": profile_url,
    }
    return render(request, "taxis/driver_profile.html", context)


def request_taxi(request):
    if request.method == "POST":
        form = RequestTaxiForm(request.POST)
        if form.is_valid():
            lead = form.save()
            messages.success(
                request,
                "Request sent to available drivers. They'll reach out on WhatsApp shortly.",
            )
            return redirect("taxis:lead_status", token=lead.token)
    else:
        form = RequestTaxiForm()
    return render(request, "taxis/request_taxi.html", {"form": form})


class DriverRequiredMixin(LoginRequiredMixin):
    """Logged in AND has a Driver profile (staff/admin accounts don't)."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and getattr(request.user, "driver", None) is None:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def driver(self):
        return self.request.user.driver


def driver_required(view_func):
    """Function-view equivalent of DriverRequiredMixin, for the views below
    that pre-date the class-based ones. Logged in AND has a Driver profile
    -- a staff/admin account that is logged in but has no Driver would
    otherwise 500 on `request.user.driver` instead of a clean 403."""
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if getattr(request.user, "driver", None) is None:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


class DirectRequestView(FormView):
    """Passenger messages ONE driver. Reuses the request-taxi fields, and the
    signal in taxis/signals.py pushes + emails the driver."""

    template_name = "taxis/direct_request.html"
    form_class = DirectRequestForm

    def dispatch(self, request, *args, **kwargs):
        self.driver = get_object_or_404(Driver, slug=kwargs["slug"], is_active_listing=True)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["driver"] = self.driver
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["driver"] = self.driver
        return context

    def form_valid(self, form):
        lead = form.save()
        messages.success(self.request, f"Request sent to {self.driver.full_name}.")
        return redirect("taxis:lead_status", token=lead.token)


class LeadStatusView(DetailView):
    """Passenger's private status page, addressed by an unguessable token
    (never the sequential lead id). Auto-refreshes while the request is open,
    which is what keeps the passenger on the platform until a driver answers."""

    slug_field = "token"
    slug_url_kwarg = "token"
    template_name = "taxis/lead_status.html"
    context_object_name = "lead"

    def get_queryset(self):
        return Lead.objects.exclude(kind=Lead.Kind.PASSIVE).select_related(
            "target_driver", "unlocked_by"
        )


class WhatsAppRedirectView(View):
    """Every WhatsApp button on the site points here instead of straight at
    wa.me, so each tap is logged as a PASSIVE lead before redirecting."""

    def get(self, request, slug):
        driver = get_object_or_404(Driver, slug=slug, is_active_listing=True)
        self._log_tap(request, driver)
        destination = driver.route_list[0] if driver.route_list else ""
        return HttpResponseRedirect(build_wa_link(driver.phone_number, hail_message(destination)))

    @staticmethod
    def _log_tap(request, driver):
        key = f"wa_tap_{driver.pk}"
        now = timezone.now().timestamp()
        last_tap = request.session.get(key)
        if last_tap and now - last_tap < settings.PASSIVE_CLICK_DEDUPE_MINUTES * 60:
            return
        request.session[key] = now
        Lead.objects.create(
            kind=Lead.Kind.PASSIVE, driver_profile_viewed=driver,
            passenger_name="", passenger_phone="", pickup="", destination="",
        )


# --- Driver auth & dashboard ---

def driver_signup(request):
    if request.method == "POST":
        form = DriverSignupForm(request.POST, request.FILES)
        if form.is_valid():
            driver = form.save()
            auth_login(request, driver.user)
            send_welcome_email(driver)
            messages.success(request, "Profile created. You're listed under Free tier — go online to start getting leads.")
            return redirect("taxis:driver_dashboard")
    else:
        form = DriverSignupForm()
    return render(request, "taxis/driver_signup.html", {"form": form})


class DriverLoginView(LoginView):
    template_name = "taxis/driver_login.html"


def driver_logout(request):
    auth_logout(request)
    return redirect("taxis:home")


@driver_required
def driver_dashboard(request):
    driver = request.user.driver
    now = timezone.now()
    open_hot_leads = Lead.objects.filter(kind=Lead.Kind.HOT, status=Lead.Status.OPEN)
    direct_requests = Lead.objects.filter(
        kind=Lead.Kind.DIRECT, target_driver=driver, status=Lead.Status.OPEN,
    )
    my_unlocked_leads = Lead.objects.filter(unlocked_by=driver).order_by("-unlocked_at")[:20]
    pending_payments = driver.payments.filter(status=Payment.Status.PENDING)
    going_to_posts = driver.going_to_posts.filter(expires_at__gt=now)

    context = {
        "driver": driver,
        "open_hot_leads": open_hot_leads,
        "direct_requests": direct_requests,
        "needs_email": not driver.email,
        "push_enabled": settings.PUSH_NOTIFICATIONS_ENABLED,
        "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        "has_push_subscription": driver.push_subscriptions.exists(),
        "free_leads_left": driver.free_leads_left(),
        "tab_balance": services.tab_balance(driver),
        "tab_due": services.tab_is_due(driver),
        "tab_pending": services.pending_settlement(driver),
        "tab_limit": services.tab_limit(),
        "wa_taps_30d": Lead.objects.filter(
            kind=Lead.Kind.PASSIVE, driver_profile_viewed=driver,
            created_at__gte=now - timedelta(days=30),
        ).count(),
        "my_unlocked_leads": my_unlocked_leads,
        "pending_payments": pending_payments,
        "going_to_posts": going_to_posts,
        "hot_lead_price": settings.HOT_LEAD_PRICE_USD,
        "pro_weekly_price": settings.PRO_WEEKLY_PRICE_USD,
        "pro_monthly_price": settings.PRO_MONTHLY_PRICE_USD,
        "going_to_pin_price": settings.GOING_TO_PIN_PRICE_USD,
    }
    return render(request, "taxis/dashboard.html", context)


@driver_required
@require_POST
def toggle_online(request):
    driver = request.user.driver
    if driver.is_online:
        driver.last_online_at = None
        messages.info(request, "You're now offline.")
    else:
        driver.last_online_at = timezone.now()
        messages.success(request, "You're online. New leads will show on your dashboard.")
    driver.save(update_fields=["last_online_at"])
    return redirect("taxis:driver_dashboard")


@driver_required
def edit_profile(request):
    driver = request.user.driver
    if request.method == "POST":
        form = DriverProfileForm(request.POST, request.FILES, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("taxis:driver_dashboard")
    else:
        form = DriverProfileForm(instance=driver)
    return render(request, "taxis/edit_profile.html", {"form": form})


UNLOCK_MESSAGES = {
    Unlock.PRO: (messages.SUCCESS, "Unlocked (free with Pro). The passenger's number is under 'Your unlocked leads'."),
    Unlock.TAKEN: (messages.WARNING, "This lead has already been taken or answered."),
    Unlock.NOT_ALLOWED: (messages.ERROR, "You can't unlock that lead."),
}


class UnlockLeadView(DriverRequiredMixin, View):
    """One endpoint for every unlock. The rules (Pro / free quota / tab) live
    in services.unlock_lead(); this only turns the outcome into a message."""

    http_method_names = ["post"]

    def post(self, request, lead_id):
        result = services.unlock_lead(lead_id, self.driver)

        if result.outcome == Unlock.FREE_QUOTA:
            left = self.driver.free_leads_left()
            messages.success(
                request,
                f"Unlocked using a free lead ({left} left this month). "
                "The passenger's number is under 'Your unlocked leads'.",
            )
        elif result.outcome == Unlock.ON_TAB:
            balance = services.tab_balance(self.driver)
            messages.success(
                request,
                f"Unlocked. ${result.charged} added to your tab (now ${balance}). "
                "The passenger's number is under 'Your unlocked leads'.",
            )
        elif result.outcome == Unlock.TAB_DUE:
            messages.warning(
                request,
                f"Your tab (${services.tab_balance(self.driver)}) is due. "
                "Settle it to keep unlocking leads.",
            )
            return redirect("taxis:tab")
        else:
            level, text = UNLOCK_MESSAGES[result.outcome]
            messages.add_message(request, level, text)
        return redirect("taxis:driver_dashboard")


class DeclineLeadView(DriverRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, lead_id):
        if services.decline_direct_request(lead_id, self.driver):
            messages.info(request, "Request declined. The passenger will see that you can't take it.")
        else:
            messages.warning(request, "That request can't be declined (already answered, or not yours).")
        return redirect("taxis:driver_dashboard")


class TabView(DriverRequiredMixin, FormView):
    """Running tab of unlocks made after the free quota. Settle any time;
    it also falls due at TAB_LIMIT_USD or TAB_MAX_DAYS (see services.py)."""

    template_name = "taxis/tab.html"
    form_class = PaymentProofForm
    success_url = reverse_lazy("taxis:driver_dashboard")

    def get_initial(self):
        return {"method": Payment.Method.ECOCASH}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "entries": services.unsettled_entries(self.driver).select_related("lead"),
            "balance": services.tab_balance(self.driver),
            "due": services.tab_is_due(self.driver),
            "pending": services.pending_settlement(self.driver),
            "can_settle": services.can_settle(self.driver),
            "tab_limit": services.tab_limit(),
            "tab_max_days": settings.TAB_MAX_DAYS,
            "lead_price": services.lead_price(),
            "free_cap": settings.FREE_TIER_LEAD_CAP,
            "paynow_enabled": settings.PAYNOW_ENABLED,
            "ecocash_merchant_number": settings.ECOCASH_MERCHANT_NUMBER,
            "ecocash_merchant_name": settings.ECOCASH_MERCHANT_NAME,
        })
        return context

    def form_valid(self, form):
        if not services.can_settle(self.driver):
            messages.info(self.request, "Nothing to settle right now, or a settlement is already awaiting confirmation.")
            return redirect("taxis:tab")
        payment = form.save(commit=False)
        payment.driver = self.driver
        payment.purpose = Payment.Purpose.TAB_SETTLEMENT
        payment.amount_usd = services.tab_balance(self.driver)
        payment.save()
        messages.success(
            self.request,
            "Settlement submitted. You can keep unlocking leads while it's being confirmed.",
        )
        return super().form_valid(form)


@driver_required
def go_pro(request):
    driver = request.user.driver
    if request.method == "POST":
        plan = request.POST.get("plan")
        purpose = Payment.Purpose.PRO_WEEKLY if plan == "weekly" else Payment.Purpose.PRO_MONTHLY
        amount = Decimal(
            settings.PRO_WEEKLY_PRICE_USD if plan == "weekly" else settings.PRO_MONTHLY_PRICE_USD
        )
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.driver = driver
            payment.purpose = purpose
            payment.amount_usd = amount
            payment.save()
            messages.success(request, "Payment submitted. Pro status activates once confirmed.")
            return redirect("taxis:driver_dashboard")
    else:
        form = PaymentProofForm(initial={"method": Payment.Method.ECOCASH})

    context = {
        "form": form,
        "weekly_price": settings.PRO_WEEKLY_PRICE_USD,
        "monthly_price": settings.PRO_MONTHLY_PRICE_USD,
        "ecocash_merchant_number": settings.ECOCASH_MERCHANT_NUMBER,
        "ecocash_merchant_name": settings.ECOCASH_MERCHANT_NAME,
        "paynow_enabled": settings.PAYNOW_ENABLED,
    }
    return render(request, "taxis/go_pro.html", context)


@driver_required
def post_going_to(request):
    driver = request.user.driver
    if not driver.is_pro and driver.monthly_going_to_cap_reached():
        messages.warning(
            request, "You've used your free 'Going To' post for this month. Go Pro for unlimited posts."
        )
        return redirect("taxis:driver_dashboard")

    if request.method == "POST":
        form = GoingToForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.driver = driver
            post.save()
            if not driver.is_pro:
                driver.going_to_used_this_month += 1
                driver.save(update_fields=["going_to_used_this_month"])
            messages.success(request, "Posted to the homepage banner for 24 hours.")
            return redirect("taxis:driver_dashboard")
    else:
        form = GoingToForm()
    return render(request, "taxis/post_going_to.html", {"form": form})


@staff_member_required
def admin_leads_dashboard(request):
    """Operational view of the thing admin actually has to babysit: open
    hot leads, pending manual EcoCash payments, and how much lead volume
    Pro drivers are already absorbing for free (the metric that shows
    whether 'minimise manual involvement' is working)."""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    context = {
        "open_hot_leads": Lead.objects.filter(kind=Lead.Kind.HOT, status=Lead.Status.OPEN).order_by("-created_at"),
        "pending_payments": Payment.objects.filter(status=Payment.Status.PENDING).select_related("driver"),
        "unlocked_today": Lead.objects.filter(status=Lead.Status.UNLOCKED, unlocked_at__gte=today_start).count(),
        "pro_claims_today": Lead.objects.filter(
            status=Lead.Status.UNLOCKED, unlocked_at__gte=today_start, unlocked_by__pro_until__gt=now
        ).count(),
        "active_pro_drivers": Driver.objects.filter(pro_until__gt=now).count(),
        "direct_requests_today": Lead.objects.filter(kind=Lead.Kind.DIRECT, created_at__gte=today_start).count(),
        "whatsapp_taps_today": Lead.objects.filter(kind=Lead.Kind.PASSIVE, created_at__gte=today_start).count(),
        "tab_outstanding": TabEntry.objects.filter(settled_by__isnull=True).aggregate(
            total=Sum("amount_usd")
        )["total"] or Decimal("0.00"),
        "online_drivers": [d for d in Driver.objects.filter(is_active_listing=True) if d.is_online],
    }
    return render(request, "admin/leads_dashboard.html", context)


def faqs(request):
    audience = request.GET.get("for", "").strip()
    faq_list = FAQ.objects.filter(is_published=True)
    if audience in (FAQ.Audience.PASSENGER, FAQ.Audience.DRIVER):
        faq_list = faq_list.filter(audience__in=[audience, FAQ.Audience.BOTH])
    return render(request, "taxis/faqs.html", {"faqs": faq_list, "audience": audience})


def service_worker(request):
    """Serve the service worker from the site root.

    A worker served from /static/ can only control /static/*, so
    navigator.serviceWorker.ready never resolves on /dashboard/ and the
    "turn on notifications" button would hang. Serving it from / (with the
    Service-Worker-Allowed header) gives it whole-site scope.
    """
    path = finders.find("service-worker.js")
    if not path:
        raise Http404("service-worker.js not found")
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    response = HttpResponse(content, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"  # browsers must re-check for updates
    return response


@driver_required
@require_POST
def push_subscribe(request):
    """Called by the dashboard's 'Enable notifications' button (see app.js).
    Body is the raw PushSubscription JSON from the browser's Push API."""
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
        keys = data["keys"]
        p256dh, auth = keys["p256dh"], keys["auth"]
    except (ValueError, KeyError, TypeError):
        return HttpResponseBadRequest("Malformed subscription payload")

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={"driver": request.user.driver, "p256dh": p256dh, "auth": auth},
    )
    return JsonResponse({"status": "subscribed"})


@driver_required
@require_POST
def push_unsubscribe(request):
    try:
        data = json.loads(request.body)
        endpoint = data["endpoint"]
    except (ValueError, KeyError, TypeError):
        return HttpResponseBadRequest("Malformed payload")

    PushSubscription.objects.filter(endpoint=endpoint, driver=request.user.driver).delete()
    return JsonResponse({"status": "unsubscribed"})
