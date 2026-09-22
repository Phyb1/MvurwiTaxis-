from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from taxis.models import Driver, GoingToPost, Lead, Payment, Review
from taxis.utils.whatsapp import normalize_phone


class DriverSignupForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        help_text="As you'd like passengers to see it, e.g. Tino Chapfika.",
    )
    phone_number = forms.CharField(
        max_length=20,
        help_text=(
            "e.g. 263775123456 — this becomes your login username. It is never "
            "shown to passengers directly; they contact you through the "
            "WhatsApp button on your profile."
        ),
    )
    email = forms.EmailField(
        help_text=(
            "Required. New passenger requests are emailed here, and it's how you "
            "reset a forgotten password."
        ),
    )
    password = forms.CharField(widget=forms.PasswordInput, help_text="At least 8 characters.")
    car_type = forms.ChoiceField(
        choices=Driver._meta.get_field("car_type").choices,
        help_text="Pick the closest match. Passengers can filter by car type.",
    )
    car_reg = forms.CharField(
        max_length=20,
        help_text="Your number plate, e.g. ADS1234.",
    )
    photo = forms.ImageField(
        required=False,
        help_text="A clear photo of your car. Listings with a photo get more clicks — you can add this later too.",
    )
    seats = forms.IntegerField(
        min_value=1, max_value=30, initial=4,
        help_text="Passenger seats, not counting yours (1-30).",
    )
    base_area = forms.CharField(
        max_length=120, initial="Mvurwi Town",
        help_text="Where you usually wait for passengers.",
    )
    routes = forms.CharField(
        max_length=255, required=False,
        help_text="Comma-separated, e.g. Harare, Bindura, NOC",
    )

    def clean_phone_number(self):
        phone = normalize_phone(self.cleaned_data["phone_number"])
        if not phone or len(phone) < 9:
            raise forms.ValidationError("Enter a valid phone number.")
        if User.objects.filter(username=phone).exists():
            raise forms.ValidationError("A driver with this number is already registered.")
        return phone

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def save(self):
        # Atomic: if Driver creation fails after the User is made (bad photo
        # file, DB constraint, etc.) we don't want an orphaned login with no
        # profile attached to it.
        with transaction.atomic():
            phone = self.cleaned_data["phone_number"]
            email = self.cleaned_data.get("email", "")
            user = User.objects.create_user(
                username=phone, email=email, password=self.cleaned_data["password"]
            )
            driver = Driver.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                phone_number=phone,
                email=email,
                photo=self.cleaned_data.get("photo"),
                car_type=self.cleaned_data["car_type"],
                car_reg=self.cleaned_data["car_reg"],
                seats=self.cleaned_data["seats"],
                base_area=self.cleaned_data["base_area"],
                routes=self.cleaned_data["routes"],
            )
        return driver


class DriverProfileForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = [
            "full_name", "email", "photo", "car_type", "car_reg", "seats",
            "base_area", "base_lat", "base_lng", "routes",
        ]
        help_texts = {
            "full_name": "As you'd like passengers to see it.",
            "email": (
                "Required. New passenger requests are emailed here, and it's how "
                "you reset a forgotten password."
            ),
            "car_type": "Pick the closest match. Passengers can filter by car type.",
            "car_reg": "Your number plate, e.g. ADS1234.",
            "seats": "Passenger seats, not counting yours.",
            "base_area": "Where you usually wait for passengers.",
            "base_lat": "Optional. Lets passengers see how far you are from them.",
            "base_lng": "Optional. Lets passengers see how far you are from them.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Model keeps blank=True so drivers who signed up before email became
        # mandatory aren't broken — but they can't save their profile without one.
        self.fields["email"].required = True

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def save(self, commit=True):
        driver = super().save(commit=commit)
        if commit:
            # Django's password-reset flow reads User.email, not Driver.email.
            driver.user.email = driver.email
            driver.user.save(update_fields=["email"])
        return driver


class LeadFormBase(forms.ModelForm):
    """Shared fields + validation for every passenger-facing request form
    ("Request Any Taxi" and "Message this driver"), so both validate — and
    explain themselves — identically."""

    people = forms.IntegerField(
        min_value=1, max_value=30, initial=1, label="Number of people",
        help_text="How many people are travelling, including you (1-30).",
    )

    class Meta:
        model = Lead
        fields = ["passenger_name", "passenger_phone", "pickup", "destination", "people", "requested_time"]
        labels = {
            "passenger_name": "Your name",
            "passenger_phone": "Your phone number",
            "requested_time": "When do you need it?",
        }
        help_texts = {
            "passenger_name": "Your first name is enough. The driver sees this first.",
            "passenger_phone": (
                "Your mobile or WhatsApp number, e.g. 0771234567. Drivers only "
                "get it once they take your request."
            ),
            "pickup": "Where the driver should collect you, e.g. OK Supermarket, Mvurwi.",
            "destination": "Where you're going, e.g. Harare CBD.",
            "requested_time": "e.g. Now, 2pm, tomorrow 7am. Leave blank for as soon as possible.",
        }
        widgets = {
            "passenger_name": forms.TextInput(attrs={"autocomplete": "given-name", "placeholder": "e.g. Rudo"}),
            "passenger_phone": forms.TextInput(
                attrs={"type": "tel", "inputmode": "tel", "autocomplete": "tel", "placeholder": "0771234567"}
            ),
            "requested_time": forms.TextInput(attrs={"placeholder": "e.g. Now, 2pm"}),
        }

    def clean_passenger_name(self):
        name = " ".join(self.cleaned_data["passenger_name"].split())
        if len(name) < 2 or not any(ch.isalpha() for ch in name):
            raise forms.ValidationError("Enter your name (at least 2 letters).")
        return name

    def clean_passenger_phone(self):
        phone = normalize_phone(self.cleaned_data["passenger_phone"])
        if not (phone.startswith("263") and len(phone) == 12):
            raise forms.ValidationError("Enter a valid Zimbabwe mobile number, e.g. 0771234567.")
        return phone

    def _clean_place(self, field_name, label):
        value = " ".join(self.cleaned_data[field_name].split())
        if len(value) < 2:
            raise forms.ValidationError(f"Enter a {label} (at least 2 characters).")
        return value

    def clean_pickup(self):
        return self._clean_place("pickup", "pickup place")

    def clean_destination(self):
        return self._clean_place("destination", "destination")

    def clean(self):
        cleaned = super().clean()
        pickup, destination = cleaned.get("pickup"), cleaned.get("destination")
        if pickup and destination and pickup.casefold() == destination.casefold():
            self.add_error("destination", "Pickup and destination can't be the same place.")
        return cleaned


class RequestTaxiForm(LeadFormBase):
    """Broadcast request: goes to every driver, first to unlock wins."""

    def save(self, commit=True):
        lead = super().save(commit=False)
        lead.kind = Lead.Kind.HOT
        if commit:
            lead.save()
        return lead


class DirectRequestForm(LeadFormBase):
    """Message request to ONE specific driver. Same fields as RequestTaxiForm
    plus an optional note; the driver is passed in by the view."""

    message = forms.CharField(
        required=False, max_length=300,
        label="Message to the driver",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "e.g. I have 2 bags. I'll wait at the fuel station."}),
        help_text="Optional. Anything the driver should know (up to 300 characters).",
    )

    class Meta(LeadFormBase.Meta):
        fields = LeadFormBase.Meta.fields + ["message"]

    def __init__(self, *args, driver, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver
        capacity = min(driver.seats, 30)
        self.fields["people"].widget.attrs["max"] = capacity
        self.fields["people"].help_text = (
            f"How many people are travelling, including you. This car seats up to {driver.seats}."
        )

    def clean_people(self):
        people = self.cleaned_data["people"]
        if people > self.driver.seats:
            raise forms.ValidationError(
                f"{self.driver.full_name}'s car seats {self.driver.seats}. "
                "Choose fewer people, or use 'Request Any Taxi' for a bigger vehicle."
            )
        return people

    def clean_message(self):
        return " ".join(self.cleaned_data["message"].split())

    def clean(self):
        cleaned = super().clean()
        phone = cleaned.get("passenger_phone")
        if phone:
            now = timezone.now()
            from_this_number = Lead.objects.filter(kind=Lead.Kind.DIRECT, passenger_phone=phone)
            duplicate_window = timedelta(minutes=settings.DIRECT_REQUEST_DUPLICATE_MINUTES)
            if from_this_number.filter(
                target_driver=self.driver, created_at__gte=now - duplicate_window
            ).exists():
                raise forms.ValidationError(
                    "You've just messaged this driver. Give them a few minutes to reply "
                    "before sending another request."
                )
            recent = from_this_number.filter(created_at__gte=now - timedelta(hours=1)).count()
            if recent >= settings.DIRECT_REQUEST_HOURLY_LIMIT:
                raise forms.ValidationError(
                    "Too many requests from this number in the last hour. Please try again later."
                )
        return cleaned

    def save(self, commit=True):
        lead = super().save(commit=False)
        lead.kind = Lead.Kind.DIRECT
        lead.target_driver = self.driver
        if commit:
            lead.save()
        return lead


class GoingToForm(forms.ModelForm):
    class Meta:
        model = GoingToPost
        fields = ["destination", "seats_available", "price_usd", "departure_text"]


class PaymentProofForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["method", "ecocash_reference", "proof_of_payment"]
        widgets = {
            "method": forms.RadioSelect,
        }
        help_texts = {
            "ecocash_reference": "The transaction reference EcoCash texts you after paying.",
            "proof_of_payment": "Or upload a screenshot of the confirmation instead.",
        }

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("method")
        reference = cleaned.get("ecocash_reference")
        proof = cleaned.get("proof_of_payment")
        # Paynow redirects to a hosted payment page and confirms itself via
        # webhook — no manual reference/proof needed from the driver.
        if method == Payment.Method.ECOCASH and not reference and not proof:
            raise forms.ValidationError(
                "Provide either an EcoCash transaction reference or a proof-of-payment screenshot."
            )
        return cleaned


class RatingWidget(forms.RadioSelect):
    """Renders as a row of star radio buttons via CSS (see .star-rating in
    style.css) rather than a plain <select> or bullet list."""
    template_name = "taxis/widgets/star_rating.html"
    option_template_name = "taxis/widgets/star_rating_option.html"


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["passenger_name", "rating", "comment"]
        widgets = {"rating": RatingWidget(choices=[(i, str(i)) for i in range(5, 0, -1)])}
        help_texts = {
            "rating": "Tap a star. 5 = excellent, 1 = poor.",
            "comment": "Optional — a line or two about your trip.",
        }
