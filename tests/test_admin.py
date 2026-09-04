import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from taxis.models import Payment


@pytest.fixture
def admin_client_logged_in(client, db):
    admin = User.objects.create_superuser("admin", "admin@example.com", "adminpass123")
    client.force_login(admin)
    return client


@pytest.mark.django_db
def test_confirm_payments_admin_action_applies_effect(admin_client_logged_in, driver_user, hot_lead):
    payment = Payment.objects.create(
        driver=driver_user, purpose=Payment.Purpose.HOT_LEAD,
        amount_usd="0.20", related_lead=hot_lead,
    )
    url = reverse("admin:taxis_payment_changelist")
    resp = admin_client_logged_in.post(url, {
        "action": "confirm_payments",
        "_selected_action": [str(payment.id)],
    }, follow=True)
    assert resp.status_code == 200
    payment.refresh_from_db()
    assert payment.status == Payment.Status.CONFIRMED
    hot_lead.refresh_from_db()
    assert hot_lead.status == "unlocked"
