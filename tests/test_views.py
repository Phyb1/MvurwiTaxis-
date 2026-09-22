import pytest
from django.urls import reverse

from taxis.models import Driver, Lead, Payment


@pytest.mark.django_db
def test_home_page_loads(client, driver_user):
    resp = client.get(reverse("taxis:home"))
    assert resp.status_code == 200
    assert b"Tino Chapfika" in resp.content


@pytest.mark.django_db
def test_home_page_filters_by_destination(client, driver_user, second_driver):
    resp = client.get(reverse("taxis:home"), {"destination": "Harare"})
    assert resp.status_code == 200
    assert b"Tino Chapfika" in resp.content
    assert b"Kuda Moyo" not in resp.content


@pytest.mark.django_db
def test_fares_page_loads(client, fare):
    resp = client.get(reverse("taxis:fares"))
    assert resp.status_code == 200
    assert b"Harare" in resp.content


@pytest.mark.django_db
def test_driver_profile_page_loads(client, driver_user):
    resp = client.get(reverse("taxis:driver_profile", args=[driver_user.slug]))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_driver_signup_creates_driver_and_logs_in(client):
    resp = client.post(reverse("taxis:driver_signup"), {
        "full_name": "New Driver",
        "phone_number": "0775333333",
        "email": "newdriver@example.com",
        "password": "strongpass123",
        "car_type": "corolla",
        "car_reg": "NEW1234",
        "seats": 4,
        "base_area": "Mvurwi Town",
        "routes": "Harare",
    })
    assert resp.status_code == 302
    assert Driver.objects.filter(phone_number="263775333333").exists()
    # Session should now be authenticated -> dashboard accessible
    dash = client.get(reverse("taxis:driver_dashboard"))
    assert dash.status_code == 200


@pytest.mark.django_db
def test_driver_signup_rejects_duplicate_phone(client, driver_user):
    resp = client.post(reverse("taxis:driver_signup"), {
        "full_name": "Dupe",
        "phone_number": "0775111111",  # same as driver_user fixture
        "password": "strongpass123",
        "car_type": "corolla",
        "car_reg": "DUP1234",
        "seats": 4,
        "base_area": "Mvurwi Town",
    })
    assert resp.status_code == 200  # re-renders form with error
    assert b"already registered" in resp.content


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    resp = client.get(reverse("taxis:driver_dashboard"))
    assert resp.status_code == 302
    assert "/login/" in resp.url


@pytest.mark.django_db
def test_toggle_online_flips_status(client, driver_user):
    client.force_login(driver_user.user)
    assert driver_user.is_online is False

    client.post(reverse("taxis:toggle_online"))
    driver_user.refresh_from_db()
    assert driver_user.is_online is True

    client.post(reverse("taxis:toggle_online"))
    driver_user.refresh_from_db()
    assert driver_user.is_online is False


@pytest.mark.django_db
def test_request_taxi_creates_hot_lead(client):
    resp = client.post(reverse("taxis:request_taxi"), {
        "passenger_name": "Rudo",
        "passenger_phone": "0771234567",
        "pickup": "Mvurwi Town",
        "destination": "Harare",
        "people": 2,
        "requested_time": "Now",
    })
    assert resp.status_code == 302
    lead = Lead.objects.get(passenger_name="Rudo")
    assert lead.kind == Lead.Kind.HOT
    assert lead.status == Lead.Status.OPEN




@pytest.mark.django_db
def test_go_pro_submits_pending_payment(client, driver_user):
    client.force_login(driver_user.user)
    resp = client.post(reverse("taxis:go_pro"), {
        "plan": "weekly", "method": "ecocash", "ecocash_reference": "EC777",
    })
    assert resp.status_code == 302
    assert Payment.objects.filter(driver=driver_user, purpose=Payment.Purpose.PRO_WEEKLY).exists()


@pytest.mark.django_db
def test_bookmark_prompt_markup_present_on_home(client):
    """The banner itself is server-rendered (hidden by default); app.js
    decides whether/when to reveal it, including skipping driver-only
    pages by pathname — see static/js/app.js::initBookmarkPrompt."""
    resp = client.get(reverse("taxis:home"))
    assert b'id="bookmark-prompt"' in resp.content
    assert b"hidden" in resp.content
    assert b'id="bookmark-prompt-accept"' in resp.content
    assert b'id="bookmark-prompt-dismiss"' in resp.content
