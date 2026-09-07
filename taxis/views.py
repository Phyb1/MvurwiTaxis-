from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from taxis.forms import (
    DriverProfileForm,
    DriverSignupForm,
    GoingToForm,
    PaymentProofForm,
    RequestTaxiForm,
    ReviewForm,
)
from taxis.models import CarType, Driver, FAQ, Fare, GoingToPost, Lead, Payment
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
        "wa_hail_link": build_wa_link(driver.phone_number, hail_message(driver.route_list[0] if driver.route_list else "")),
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
            return redirect("taxis:request_taxi_sent", lead_id=lead.id)
    else:
        form = RequestTaxiForm()
    return render(request, "taxis/request_taxi.html", {"form": form})


def request_taxi_sent(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    return render(request, "taxis/request_taxi_sent.html", {"lead": lead})


# --- Driver auth & dashboard ---

def driver_signup(request):
    if request.method == "POST":
        form = DriverSignupForm(request.POST, request.FILES)
        if form.is_valid():
            driver = form.save()
            auth_login(request, driver.user)
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


@login_required
def driver_dashboard(request):
    driver = request.user.driver
    open_hot_leads = Lead.objects.filter(kind=Lead.Kind.HOT, status=Lead.Status.OPEN)
    my_unlocked_leads = Lead.objects.filter(unlocked_by=driver).order_by("-unlocked_at")[:20]
    pending_payments = driver.payments.filter(status=Payment.Status.PENDING)
    going_to_posts = driver.going_to_posts.filter(expires_at__gt=timezone.now())

    context = {
        "driver": driver,
        "open_hot_leads": open_hot_leads,
        "my_unlocked_leads": my_unlocked_leads,
        "pending_payments": pending_payments,
        "going_to_posts": going_to_posts,
        "hot_lead_price": settings.HOT_LEAD_PRICE_USD,
        "pro_weekly_price": settings.PRO_WEEKLY_PRICE_USD,
        "pro_monthly_price": settings.PRO_MONTHLY_PRICE_USD,
        "going_to_pin_price": settings.GOING_TO_PIN_PRICE_USD,
    }
    return render(request, "taxis/dashboard.html", context)


@login_required
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


@login_required
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


@login_required
def unlock_lead(request, lead_id):
    driver = request.user.driver
    lead = get_object_or_404(Lead, id=lead_id, kind=Lead.Kind.HOT)

    if not lead.is_open_for_unlock():
        messages.warning(request, "This lead has already been taken.")
        return redirect("taxis:driver_dashboard")

    if driver.monthly_lead_cap_reached():
        messages.warning(
            request,
            "You've used your free leads for this month. Go Pro for unlimited leads.",
        )
        return redirect("taxis:driver_dashboard")

    if request.method == "POST":
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.driver = driver
            payment.purpose = Payment.Purpose.HOT_LEAD
            payment.amount_usd = Decimal(settings.HOT_LEAD_PRICE_USD)
            payment.related_lead = lead
            payment.save()
            messages.success(
                request,
                "Payment submitted. It will be confirmed shortly and the lead unlocked.",
            )
            return redirect("taxis:driver_dashboard")
    else:
        form = PaymentProofForm(initial={"method": Payment.Method.ECOCASH})

    context = {
        "form": form,
        "lead": lead,
        "amount": settings.HOT_LEAD_PRICE_USD,
        "ecocash_merchant_number": settings.ECOCASH_MERCHANT_NUMBER,
        "ecocash_merchant_name": settings.ECOCASH_MERCHANT_NAME,
        "paynow_enabled": settings.PAYNOW_ENABLED,
    }
    return render(request, "taxis/unlock_lead.html", context)


@login_required
def claim_lead_pro(request, lead_id):
    """Pro drivers unlock leads for free — no EcoCash step, no admin
    confirmation needed. This is the main way manual involvement in lead
    processing is minimised; see taxis/signals.py for the matching
    notification half of the flow."""
    driver = request.user.driver
    lead = get_object_or_404(Lead, id=lead_id, kind=Lead.Kind.HOT)

    if not driver.is_pro:
        messages.warning(request, "Claiming leads for free is a Pro feature.")
        return redirect("taxis:driver_dashboard")

    if not lead.is_open_for_unlock():
        messages.warning(request, "This lead has already been taken.")
        return redirect("taxis:driver_dashboard")

    lead.status = Lead.Status.UNLOCKED
    lead.unlocked_by = driver
    lead.unlocked_at = timezone.now()
    lead.save(update_fields=["status", "unlocked_by", "unlocked_at"])
    messages.success(request, "Lead claimed — the passenger's number is on your dashboard.")
    return redirect("taxis:driver_dashboard")


@login_required
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


@login_required
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
        "online_drivers": [d for d in Driver.objects.filter(is_active_listing=True) if d.is_online],
    }
    return render(request, "admin/leads_dashboard.html", context)


def faqs(request):
    audience = request.GET.get("for", "").strip()
    faq_list = FAQ.objects.filter(is_published=True)
    if audience in (FAQ.Audience.PASSENGER, FAQ.Audience.DRIVER):
        faq_list = faq_list.filter(audience__in=[audience, FAQ.Audience.BOTH])
    return render(request, "taxis/faqs.html", {"faqs": faq_list, "audience": audience})
