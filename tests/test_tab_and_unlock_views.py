"""HTTP layer over taxis/services.py: UnlockLeadView, TabView, and the
tracked WhatsApp redirect that replaced the old direct wa.me links."""
from decimal import Decimal

import pytest
from django.urls import reverse

from taxis.models import Driver, Lead, Payment, TabEntry

pytestmark = pytest.mark.django_db


# --- unlock ---

def test_unlock_free_quota_shows_success_message(client, driver_user, hot_lead):
    client.force_login(driver_user.user)
    resp = client.post(reverse("taxis:unlock_lead", args=[hot_lead.id]), follow=True)
    assert b"free lead" in resp.content
    hot_lead.refresh_from_db()
    assert hot_lead.status == Lead.Status.UNLOCKED


def test_unlock_past_quota_charges_the_tab_and_says_so(client, driver_user, hot_lead, use_up_free_quota):
    use_up_free_quota(driver_user)
    client.force_login(driver_user.user)
    resp = client.post(reverse("taxis:unlock_lead", args=[hot_lead.id]), follow=True)
    assert b"added to your tab" in resp.content
    assert TabEntry.objects.filter(driver=driver_user).exists()


def test_unlock_when_tab_is_due_redirects_to_tab_page(
    client, driver_user, new_hot_lead, use_up_free_quota, settings,
):
    settings.TAB_LIMIT_USD = "0.20"
    use_up_free_quota(driver_user)
    client.force_login(driver_user.user)
    client.post(reverse("taxis:unlock_lead", args=[new_hot_lead().id]))  # first charge, tab now due

    resp = client.post(reverse("taxis:unlock_lead", args=[new_hot_lead().id]))
    assert resp.status_code == 302
    assert resp.url == reverse("taxis:tab")


def test_unlock_requires_login(client, hot_lead):
    resp = client.post(reverse("taxis:unlock_lead", args=[hot_lead.id]))
    assert resp.status_code == 302
    assert "/login/" in resp.url


def test_get_is_not_allowed_on_unlock(client, driver_user, hot_lead):
    client.force_login(driver_user.user)
    resp = client.get(reverse("taxis:unlock_lead", args=[hot_lead.id]))
    assert resp.status_code == 405


def test_dashboard_visible_to_driver_without_a_driver_profile_raises_403(client):
    from django.contrib.auth.models import User
    staff = User.objects.create_user(username="staffonly", password="testpass123")
    client.force_login(staff)
    resp = client.get(reverse("taxis:driver_dashboard"))
    assert resp.status_code == 403


# --- tab settlement ---

def test_tab_page_lists_unsettled_entries_and_balance(client, driver_user, hot_lead, use_up_free_quota):
    use_up_free_quota(driver_user)
    client.force_login(driver_user.user)
    client.post(reverse("taxis:unlock_lead", args=[hot_lead.id]))

    resp = client.get(reverse("taxis:tab"))
    assert resp.status_code == 200
    assert b"0.20" in resp.content


def test_settling_the_tab_creates_a_pending_settlement_payment(
    client, driver_user, hot_lead, use_up_free_quota,
):
    use_up_free_quota(driver_user)
    client.force_login(driver_user.user)
    client.post(reverse("taxis:unlock_lead", args=[hot_lead.id]))

    resp = client.post(reverse("taxis:tab"), {"method": "ecocash", "ecocash_reference": "EC555"})
    assert resp.status_code == 302
    payment = Payment.objects.get(driver=driver_user, purpose=Payment.Purpose.TAB_SETTLEMENT)
    assert payment.status == Payment.Status.PENDING
    assert payment.amount_usd == Decimal("0.20")


def test_settling_with_nothing_owed_does_not_create_a_payment(client, driver_user):
    client.force_login(driver_user.user)
    resp = client.post(reverse("taxis:tab"), {"method": "ecocash", "ecocash_reference": "EC555"})
    assert resp.status_code == 302
    assert not Payment.objects.filter(driver=driver_user, purpose=Payment.Purpose.TAB_SETTLEMENT).exists()


def test_confirming_a_settlement_payment_clears_the_earlier_entries(
    client, driver_user, hot_lead, use_up_free_quota,
):
    use_up_free_quota(driver_user)
    client.force_login(driver_user.user)
    client.post(reverse("taxis:unlock_lead", args=[hot_lead.id]))
    client.post(reverse("taxis:tab"), {"method": "ecocash", "ecocash_reference": "EC555"})

    payment = Payment.objects.get(driver=driver_user, purpose=Payment.Purpose.TAB_SETTLEMENT)
    payment.confirm()

    assert TabEntry.objects.get(driver=driver_user).settled_by == payment
    from taxis import services
    assert services.tab_balance(driver_user) == Decimal("0.00")


# --- welcome email on signup ---

def test_signup_with_email_sends_a_welcome_email(client):
    from django.core import mail
    client.post(reverse("taxis:driver_signup"), {
        "full_name": "Fresh Driver", "phone_number": "0775999999",
        "email": "fresh@example.com", "password": "strongpass123",
        "car_type": "hiace", "car_reg": "FR1234", "seats": 4, "base_area": "Mvurwi Town",
    })
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["fresh@example.com"]
    assert "onboarding" in mail.outbox[0].subject.lower() or "steps" in mail.outbox[0].subject.lower()


# --- tracked WhatsApp redirect ---

def test_whatsapp_redirect_logs_a_passive_lead_and_redirects_to_wa_me(client, driver_user):
    resp = client.get(reverse("taxis:whatsapp_redirect", args=[driver_user.slug]))
    assert resp.status_code == 302
    assert resp.url.startswith("https://wa.me/263775111111")
    assert Lead.objects.filter(kind=Lead.Kind.PASSIVE, driver_profile_viewed=driver_user).count() == 1


def test_whatsapp_redirect_dedupes_within_the_same_session(client, driver_user):
    client.get(reverse("taxis:whatsapp_redirect", args=[driver_user.slug]))
    client.get(reverse("taxis:whatsapp_redirect", args=[driver_user.slug]))
    assert Lead.objects.filter(kind=Lead.Kind.PASSIVE, driver_profile_viewed=driver_user).count() == 1


def test_whatsapp_redirect_404s_for_delisted_driver(client, driver_user):
    driver_user.is_active_listing = False
    driver_user.save()
    resp = client.get(reverse("taxis:whatsapp_redirect", args=[driver_user.slug]))
    assert resp.status_code == 404
