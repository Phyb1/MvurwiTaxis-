from django import forms
from django.contrib.auth.models import User

from taxis.models import Driver, GoingToPost, Lead, Payment, Review
from taxis.utils.whatsapp import normalize_phone


class DriverSignupForm(forms.Form):
    full_name = forms.CharField(max_length=120)
    phone_number = forms.CharField(max_length=20, help_text="e.g. 0775123456")
    password = forms.CharField(widget=forms.PasswordInput)
    car_type = forms.ChoiceField(choices=Driver._meta.get_field("car_type").choices)
    car_reg = forms.CharField(max_length=20)
    seats = forms.IntegerField(min_value=1, max_value=30, initial=4)
    base_area = forms.CharField(max_length=120, initial="Mvurwi Town")
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

    def save(self):
        phone = self.cleaned_data["phone_number"]
        user = User.objects.create_user(
            username=phone, password=self.cleaned_data["password"]
        )
        driver = Driver.objects.create(
            user=user,
            full_name=self.cleaned_data["full_name"],
            phone_number=phone,
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
            "full_name", "photo", "car_type", "car_reg", "seats",
            "base_area", "base_lat", "base_lng", "routes",
        ]


class RequestTaxiForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["passenger_name", "passenger_phone", "pickup", "destination", "people", "requested_time"]
        widgets = {
            "requested_time": forms.TextInput(attrs={"placeholder": "e.g. Now, 2pm"}),
        }

    def save(self, commit=True):
        lead = super().save(commit=False)
        lead.kind = Lead.Kind.HOT
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

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("method")
        reference = cleaned.get("ecocash_reference")
        proof = cleaned.get("proof_of_payment")
        if method == Payment.Method.ECOCASH and not reference and not proof:
            raise forms.ValidationError(
                "Provide either an EcoCash transaction reference or a proof-of-payment screenshot."
            )
        return cleaned


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["passenger_name", "rating", "comment"]
