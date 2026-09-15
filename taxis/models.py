from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from taxis.utils.geo import haversine_km
from taxis.utils.images import compress_image


class CarType(models.TextChoices):
    HIACE = "hiace", "Hiace"
    COROLLA = "corolla", "Corolla"
    WISH = "wish", "Wish"
    OTHER = "other", "Other"


class Driver(models.Model):
    """A driver/owner profile. Auth is via Django User (phone-based username)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="driver"
    )
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(
        max_length=20,
        help_text="Your phone number, used to log in (e.g. 0775123456). "
                   "This is stored as your username — passengers never see it directly; "
                   "they reach you through the WhatsApp button.",
    )
    email = models.EmailField(
        blank=True,
        help_text="Optional, but needed if you ever want to reset your password by email.",
    )
    photo = models.ImageField(
        upload_to="drivers/photos/", blank=True, null=True,
        help_text="A clear photo of your car. Listings with a photo get more clicks.",
    )
    car_type = models.CharField(max_length=20, choices=CarType.choices, default=CarType.HIACE)
    car_reg = models.CharField(max_length=20)
    seats = models.PositiveSmallIntegerField(default=4)
    base_area = models.CharField(max_length=120, default="Mvurwi Town")
    base_lat = models.FloatField(null=True, blank=True)
    base_lng = models.FloatField(null=True, blank=True)
    routes = models.CharField(
        max_length=255, blank=True, help_text="Comma-separated, e.g. Harare, Bindura, NOC"
    )

    is_verified = models.BooleanField(default=False)
    is_active_listing = models.BooleanField(default=True)

    pro_until = models.DateTimeField(null=True, blank=True)
    last_online_at = models.DateTimeField(null=True, blank=True)

    leads_used_this_month = models.PositiveIntegerField(default=0)
    leads_reset_at = models.DateTimeField(default=timezone.now)
    going_to_used_this_month = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_verified", "-pro_until", "full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.car_reg})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.full_name}-{self.car_reg}")[:70]
            slug = base_slug
            n = 1
            while Driver.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base_slug}-{n}"
            self.slug = slug
        # FieldFile._committed is False only for a newly-assigned upload that
        # hasn't hit storage yet — this is how we avoid recompressing an
        # already-saved photo on every unrelated field update.
        if self.photo and not self.photo._committed:
            self.photo = compress_image(self.photo)
        super().save(*args, **kwargs)

    @property
    def is_pro(self):
        return bool(self.pro_until and self.pro_until > timezone.now())

    @property
    def is_online(self):
        if not self.last_online_at:
            return False
        window = timezone.timedelta(minutes=settings.ONLINE_STATUS_WINDOW_MINUTES)
        return timezone.now() - self.last_online_at <= window

    @property
    def route_list(self):
        return [r.strip() for r in self.routes.split(",") if r.strip()]

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(models.Avg("rating"))
        return round(agg["rating__avg"], 1) if agg["rating__avg"] else None

    def distance_km_from(self, lat, lng):
        if self.base_lat is None or self.base_lng is None or lat is None or lng is None:
            return None
        return haversine_km(lat, lng, self.base_lat, self.base_lng)

    def monthly_lead_cap_reached(self):
        self._maybe_reset_monthly_counters()
        if self.is_pro:
            return False
        return self.leads_used_this_month >= settings.FREE_TIER_LEAD_CAP

    def monthly_going_to_cap_reached(self):
        self._maybe_reset_monthly_counters()
        if self.is_pro:
            return False
        return self.going_to_used_this_month >= settings.FREE_TIER_GOING_TO_CAP

    def _maybe_reset_monthly_counters(self):
        if timezone.now() - self.leads_reset_at >= timezone.timedelta(days=30):
            self.leads_used_this_month = 0
            self.going_to_used_this_month = 0
            self.leads_reset_at = timezone.now()
            self.save(update_fields=[
                "leads_used_this_month", "going_to_used_this_month", "leads_reset_at"
            ])

    def whatsapp_link(self, message=""):
        from taxis.utils.whatsapp import build_wa_link
        return build_wa_link(self.phone_number, message)


class Fare(models.Model):
    """Official route price, admin-editable single source of truth."""

    origin = models.CharField(max_length=80, default="Mvurwi")
    destination = models.CharField(max_length=80)
    price_usd = models.DecimalField(max_digits=6, decimal_places=2)
    notes = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "destination"]
        unique_together = ("origin", "destination")

    def __str__(self):
        return f"{self.origin} -> {self.destination}: ${self.price_usd}"


class Lead(models.Model):
    """A passenger request. Passive leads are untracked WhatsApp clicks;
    Hot leads are logged requests that a driver pays to unlock."""

    class Kind(models.TextChoices):
        PASSIVE = "passive", "Passive"
        HOT = "hot", "Hot"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        UNLOCKED = "unlocked", "Unlocked"
        EXPIRED = "expired", "Expired"

    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.HOT)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    passenger_name = models.CharField(max_length=80)
    passenger_phone = models.CharField(max_length=20)
    pickup = models.CharField(max_length=120)
    destination = models.CharField(max_length=120)
    people = models.PositiveSmallIntegerField(default=1)
    requested_time = models.CharField(max_length=80, blank=True, help_text="Free text, e.g. 'Now', '2pm'")

    driver_profile_viewed = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="passive_leads_seen",
        help_text="Set only for passive leads originating from a specific driver profile.",
    )
    unlocked_by = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name="hot_leads_won"
    )
    unlocked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} lead: {self.pickup} -> {self.destination}"

    def is_open_for_unlock(self):
        return self.kind == self.Kind.HOT and self.status == self.Status.OPEN


class Payment(models.Model):
    """Every payment is manual EcoCash-first, Paynow as a secondary/automated
    fallback. Manual payments require admin confirmation before they take effect."""

    class Purpose(models.TextChoices):
        HOT_LEAD = "hot_lead", "Hot Lead Unlock"
        PRO_WEEKLY = "pro_weekly", "Pro Subscription (Weekly)"
        PRO_MONTHLY = "pro_monthly", "Pro Subscription (Monthly)"
        GOING_TO_PIN = "going_to_pin", "Going-To Pin"

    class Method(models.TextChoices):
        ECOCASH = "ecocash", "EcoCash (manual)"
        PAYNOW = "paynow", "Paynow"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="payments")
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.ECOCASH)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)

    amount_usd = models.DecimalField(max_digits=6, decimal_places=2)
    ecocash_reference = models.CharField(max_length=40, blank=True)
    proof_of_payment = models.ImageField(upload_to="payments/proof/", blank=True, null=True)

    related_lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.driver} - {self.get_purpose_display()} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Apply confirmation effects (unlock lead / extend Pro) the moment
        status transitions to CONFIRMED — regardless of whether that came
        from the admin's bulk 'confirm_payments' action or from an admin
        just editing the status field directly on the change form and
        hitting save. Both paths must behave identically."""
        previous_status = None
        if self.pk:
            previous_status = (
                Payment.objects.filter(pk=self.pk).values_list("status", flat=True).first()
            )
        newly_confirmed = (
            self.status == self.Status.CONFIRMED and previous_status != self.Status.CONFIRMED
        )
        if newly_confirmed and not self.confirmed_at:
            self.confirmed_at = timezone.now()

        if self.proof_of_payment and not self.proof_of_payment._committed:
            self.proof_of_payment = compress_image(self.proof_of_payment)

        super().save(*args, **kwargs)

        if newly_confirmed:
            self._apply_confirmation_effects()

    def _apply_confirmation_effects(self):
        if self.purpose == self.Purpose.HOT_LEAD and self.related_lead:
            lead = self.related_lead
            if lead.status == Lead.Status.OPEN:
                lead.status = Lead.Status.UNLOCKED
                lead.unlocked_by = self.driver
                lead.unlocked_at = timezone.now()
                lead.save(update_fields=["status", "unlocked_by", "unlocked_at"])
                self.driver.leads_used_this_month += 1
                self.driver.save(update_fields=["leads_used_this_month"])
        elif self.purpose == self.Purpose.PRO_WEEKLY:
            self._extend_pro(days=7)
        elif self.purpose == self.Purpose.PRO_MONTHLY:
            self._extend_pro(days=30)

    def confirm(self):
        """Convenience method for callers that just want to mark a payment
        confirmed — e.g. the admin bulk action, or tests. The actual effect
        application lives in save()/_apply_confirmation_effects() so it
        fires the same way no matter how status=CONFIRMED gets set."""
        if self.status != self.Status.CONFIRMED:
            self.status = self.Status.CONFIRMED
            self.save()

    def _extend_pro(self, days):
        now = timezone.now()
        base = self.driver.pro_until if self.driver.pro_until and self.driver.pro_until > now else now
        self.driver.pro_until = base + timezone.timedelta(days=days)
        self.driver.save(update_fields=["pro_until"])


class GoingToPost(models.Model):
    """'Going to X, N seats, $Y' banner post, live for 24hrs."""

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="going_to_posts")
    destination = models.CharField(max_length=120)
    seats_available = models.PositiveSmallIntegerField()
    price_usd = models.DecimalField(max_digits=6, decimal_places=2)
    departure_text = models.CharField(max_length=80, help_text="Free text, e.g. '2pm today'")
    is_pinned_paid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.driver.full_name} -> {self.destination}"

    @property
    def is_live(self):
        return timezone.now() < self.expires_at


class Review(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="reviews")
    passenger_name = models.CharField(max_length=80, blank=True, default="Anonymous")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.driver} - {self.rating}*"


class PushSubscription(models.Model):
    """Browser Web Push subscription for a driver's device. A driver can
    have more than one (phone + a second device), so this isn't OneToOne."""

    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Push subscription for {self.driver}"

    def as_subscription_info(self):
        return {"endpoint": self.endpoint, "keys": {"p256dh": self.p256dh, "auth": self.auth}}


class FAQ(models.Model):
    class Audience(models.TextChoices):
        PASSENGER = "passenger", "Passenger"
        DRIVER = "driver", "Driver"
        BOTH = "both", "Both"

    question = models.CharField(max_length=200)
    answer = models.TextField()
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.BOTH)
    order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "question"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
