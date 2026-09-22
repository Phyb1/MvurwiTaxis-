from datetime import timedelta

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from taxis.models import FAQ, Driver, Lead, Payment


@pytest.mark.django_db
def test_faqs_page_loads_and_filters(client):
    FAQ.objects.create(question="Passenger Q", answer="A", audience=FAQ.Audience.PASSENGER)
    FAQ.objects.create(question="Driver Q", answer="A", audience=FAQ.Audience.DRIVER)

    resp = client.get(reverse("taxis:faqs"))
    assert b"Passenger Q" in resp.content and b"Driver Q" in resp.content

    resp = client.get(reverse("taxis:faqs"), {"for": "driver"})
    assert b"Driver Q" in resp.content
    assert b"Passenger Q" not in resp.content


@pytest.mark.django_db
def test_unpublished_faq_hidden(client):
    FAQ.objects.create(question="Hidden", answer="A", is_published=False)
    resp = client.get(reverse("taxis:faqs"))
    assert b"Hidden" not in resp.content





@pytest.mark.django_db
def test_driver_signup_captures_email(client):
    client.post(reverse("taxis:driver_signup"), {
        "full_name": "Email Driver", "phone_number": "0775444444", "email": "driver@example.com",
        "password": "strongpass123", "car_type": "hiace", "car_reg": "EM1234",
        "seats": 4, "base_area": "Mvurwi Town",
    })
    driver = Driver.objects.get(phone_number="263775444444")
    assert driver.email == "driver@example.com"
    assert driver.user.email == "driver@example.com"


@pytest.mark.django_db
def test_driver_signup_requires_email(client):
    """Email became required once direct-message alerts needed somewhere to
    go (taxis/forms.py::DriverSignupForm) -- signup without one now fails
    validation instead of silently creating an unreachable driver."""
    resp = client.post(reverse("taxis:driver_signup"), {
        "full_name": "No Email Driver", "phone_number": "0775555555",
        "password": "strongpass123", "car_type": "hiace", "car_reg": "NE1234",
        "seats": 4, "base_area": "Mvurwi Town",
    })
    assert resp.status_code == 200
    assert not Driver.objects.filter(phone_number="263775555555").exists()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_hot_lead_notifies_pro_drivers_by_email(driver_user, second_driver):
    driver_user.pro_until = timezone.now() + timedelta(days=5)
    driver_user.email = "pro@example.com"
    driver_user.save()
    # second_driver is free-tier and has no email — should NOT be notified.

    Lead.objects.create(
        kind=Lead.Kind.HOT, passenger_name="Rudo", passenger_phone="0771234567",
        pickup="Mvurwi Town", destination="Harare",
    )

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["pro@example.com"]


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_passive_lead_does_not_notify(driver_user):
    driver_user.pro_until = timezone.now() + timedelta(days=5)
    driver_user.email = "pro@example.com"
    driver_user.save()

    Lead.objects.create(
        kind=Lead.Kind.PASSIVE, passenger_name="x", passenger_phone="y", pickup="a", destination="b",
    )
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_pages_load(client):
    assert client.get(reverse("password_reset")).status_code == 200
    assert client.get(reverse("password_reset_done")).status_code == 200
    assert client.get(reverse("password_reset_complete")).status_code == 200
