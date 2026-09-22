"""Passenger -> one driver: form, notification, and status-page views
(taxis/forms.DirectRequestForm, taxis/views.DirectRequestView/LeadStatusView/
DeclineLeadView, taxis/signals._notify_target_driver)."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from taxis.models import Lead

pytestmark = pytest.mark.django_db

VALID_PAYLOAD = {
    "passenger_name": "Rudo",
    "passenger_phone": "0771234567",
    "pickup": "Mvurwi Town",
    "destination": "Harare",
    "people": 2,
    "requested_time": "Now",
    "message": "I have 2 bags, waiting at the fuel station.",
}


def _url(driver):
    return reverse("taxis:direct_request", args=[driver.slug])


# --- the form/view ---

def test_message_form_creates_a_direct_lead_targeting_that_driver(client, driver_user):
    resp = client.post(_url(driver_user), VALID_PAYLOAD)
    lead = Lead.objects.get(passenger_name="Rudo")

    assert resp.status_code == 302
    assert resp.url == reverse("taxis:lead_status", args=[lead.token])
    assert lead.kind == Lead.Kind.DIRECT
    assert lead.target_driver == driver_user
    assert lead.status == Lead.Status.OPEN
    assert lead.message == "I have 2 bags, waiting at the fuel station."


def test_message_form_rejects_more_people_than_the_car_seats(client, driver_user):
    payload = {**VALID_PAYLOAD, "people": driver_user.seats + 1}
    resp = client.post(_url(driver_user), payload)
    assert resp.status_code == 200
    assert b"seats" in resp.content
    assert not Lead.objects.filter(passenger_name="Rudo").exists()


def test_message_form_rejects_pickup_same_as_destination(client, driver_user):
    payload = {**VALID_PAYLOAD, "destination": VALID_PAYLOAD["pickup"]}
    resp = client.post(_url(driver_user), payload)
    assert resp.status_code == 200
    assert b"can&#x27;t be the same place" in resp.content or b"can't be the same place" in resp.content


def test_message_form_blocks_duplicate_within_dedupe_window(client, driver_user):
    client.post(_url(driver_user), VALID_PAYLOAD)
    resp = client.post(_url(driver_user), VALID_PAYLOAD)
    assert resp.status_code == 200
    assert b"just messaged this driver" in resp.content
    assert Lead.objects.filter(passenger_name="Rudo").count() == 1


def test_message_form_same_passenger_can_message_a_different_driver(client, driver_user, second_driver):
    client.post(_url(driver_user), VALID_PAYLOAD)
    resp = client.post(_url(second_driver), VALID_PAYLOAD)
    assert resp.status_code == 302
    assert Lead.objects.filter(passenger_name="Rudo").count() == 2


def test_message_form_blocks_after_hourly_limit(client, driver_user, second_driver, settings):
    settings.DIRECT_REQUEST_HOURLY_LIMIT = 2
    settings.DIRECT_REQUEST_DUPLICATE_MINUTES = 0  # isolate the hourly check
    Lead.objects.create(
        kind=Lead.Kind.DIRECT, target_driver=driver_user, passenger_name="Rudo",
        passenger_phone="263771234567", pickup="a", destination="b",
    )
    Lead.objects.create(
        kind=Lead.Kind.DIRECT, target_driver=second_driver, passenger_name="Rudo",
        passenger_phone="263771234567", pickup="a", destination="b",
    )
    resp = client.post(_url(driver_user), VALID_PAYLOAD)
    assert resp.status_code == 200
    assert b"Too many requests" in resp.content


def test_message_form_rejects_inactive_driver_with_404(client, driver_user):
    driver_user.is_active_listing = False
    driver_user.save()
    resp = client.post(_url(driver_user), VALID_PAYLOAD)
    assert resp.status_code == 404


# --- notification (taxis/signals.py -> taxis/utils/notify.py) ---

@pytest.mark.parametrize("has_email", [True, False])
def test_creating_a_direct_lead_emails_the_target_driver_only(
    driver_user, second_driver, has_email,
):
    if has_email:
        driver_user.email = "tino@example.com"
        driver_user.save()

    Lead.objects.create(
        kind=Lead.Kind.DIRECT, target_driver=driver_user, passenger_name="Rudo",
        passenger_phone="263771234567", pickup="Mvurwi Town", destination="Harare",
        people=2, message="2 bags",
    )

    if has_email:
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["tino@example.com"]
        assert "Rudo" in mail.outbox[0].subject
        assert "2 bags" in mail.outbox[0].body
    else:
        assert len(mail.outbox) == 0  # no address on file -> best-effort skip, no crash


def test_creating_a_direct_lead_never_puts_the_phone_number_in_the_email(driver_user):
    driver_user.email = "tino@example.com"
    driver_user.save()
    Lead.objects.create(
        kind=Lead.Kind.DIRECT, target_driver=driver_user, passenger_name="Rudo",
        passenger_phone="263771234567", pickup="a", destination="b",
    )
    assert "263771234567" not in mail.outbox[0].body


def test_creating_a_direct_lead_calls_send_push_for_each_subscription(driver_user, settings):
    settings.PUSH_NOTIFICATIONS_ENABLED = True
    driver_user.push_subscriptions.create(
        endpoint="https://fcm.example/1", p256dh="k1", auth="a1",
    )
    driver_user.push_subscriptions.create(
        endpoint="https://fcm.example/2", p256dh="k2", auth="a2",
    )
    with patch("taxis.utils.notify.send_push", return_value=True) as mocked:
        Lead.objects.create(
            kind=Lead.Kind.DIRECT, target_driver=driver_user, passenger_name="Rudo",
            passenger_phone="263771234567", pickup="a", destination="b",
        )
    assert mocked.call_count == 2


def test_a_dead_email_backend_does_not_break_lead_creation(driver_user):
    """notify_driver is best-effort: a broken send must never bubble up and
    fail the passenger's request (see taxis/utils/notify.py)."""
    driver_user.email = "tino@example.com"
    driver_user.save()
    with patch("taxis.utils.notify.send_mail", side_effect=OSError("smtp down")):
        lead = Lead.objects.create(
            kind=Lead.Kind.DIRECT, target_driver=driver_user, passenger_name="Rudo",
            passenger_phone="263771234567", pickup="a", destination="b",
        )
    assert lead.pk is not None  # the lead itself was still created


# --- passenger status page ---

def test_lead_status_page_shows_open_state(client, direct_lead):
    resp = client.get(reverse("taxis:lead_status", args=[direct_lead.token]))
    assert resp.status_code == 200
    assert b"Waiting for" in resp.content


def test_lead_status_page_offers_whatsapp_once_reply_is_overdue(client, direct_lead, settings):
    settings.DIRECT_REQUEST_REPLY_MINUTES = 30
    Lead.objects.filter(pk=direct_lead.pk).update(
        created_at=timezone.now() - timedelta(minutes=31)
    )
    resp = client.get(reverse("taxis:lead_status", args=[direct_lead.token]))
    assert b"No reply yet" in resp.content


def test_lead_status_page_is_keyed_by_token_not_by_id(client, direct_lead):
    """A sequential id would let anyone page through other passengers'
    requests by incrementing the URL; the UUID token doesn't."""
    resp = client.get(reverse("taxis:lead_status", args=[direct_lead.token]))
    assert resp.status_code == 200
    path = resp.request["PATH_INFO"]
    assert str(direct_lead.token) in path
    assert f"/{direct_lead.id}/" not in path  # no route resolves the bare pk


def test_lead_status_page_404s_for_an_unknown_token(client):
    import uuid
    resp = client.get(reverse("taxis:lead_status", args=[uuid.uuid4()]))
    assert resp.status_code == 404


def test_lead_status_page_hides_passive_leads(client, driver_user):
    passive = Lead.objects.create(
        kind=Lead.Kind.PASSIVE, driver_profile_viewed=driver_user,
        passenger_name="", passenger_phone="", pickup="", destination="",
    )
    resp = client.get(reverse("taxis:lead_status", args=[passive.token]))
    assert resp.status_code == 404


# --- decline ---

def test_target_driver_can_decline(client, driver_user, direct_lead):
    client.force_login(driver_user.user)
    resp = client.post(reverse("taxis:decline_lead", args=[direct_lead.id]))
    assert resp.status_code == 302
    direct_lead.refresh_from_db()
    assert direct_lead.status == Lead.Status.DECLINED


def test_other_driver_cannot_decline(client, second_driver, direct_lead):
    client.force_login(second_driver.user)
    resp = client.post(reverse("taxis:decline_lead", args=[direct_lead.id]))
    direct_lead.refresh_from_db()
    assert direct_lead.status == Lead.Status.OPEN


def test_decline_requires_login(client, direct_lead):
    resp = client.post(reverse("taxis:decline_lead", args=[direct_lead.id]))
    assert resp.status_code == 302
    assert "/login/" in resp.url
