from decimal import Decimal

import pytest
from django.utils import timezone

from taxis.models import Lead, Payment


def test_hot_lead_starts_open(hot_lead):
    assert hot_lead.status == Lead.Status.OPEN
    assert hot_lead.is_open_for_unlock() is True


def test_passive_lead_not_unlockable(db):
    passive = Lead.objects.create(
        kind=Lead.Kind.PASSIVE, passenger_name="x", passenger_phone="y",
        pickup="a", destination="b",
    )
    assert passive.is_open_for_unlock() is False


def test_payment_confirm_unlocks_hot_lead(driver_user, hot_lead):
    payment = Payment.objects.create(
        driver=driver_user,
        purpose=Payment.Purpose.HOT_LEAD,
        method=Payment.Method.ECOCASH,
        amount_usd=Decimal("0.20"),
        ecocash_reference="EC12345",
        related_lead=hot_lead,
    )
    payment.confirm()

    hot_lead.refresh_from_db()
    driver_user.refresh_from_db()

    assert hot_lead.status == Lead.Status.UNLOCKED
    assert hot_lead.unlocked_by == driver_user
    assert hot_lead.unlocked_at is not None
    assert driver_user.leads_used_this_month == 1
    assert payment.status == Payment.Status.CONFIRMED


def test_payment_confirm_is_idempotent(driver_user, hot_lead):
    payment = Payment.objects.create(
        driver=driver_user, purpose=Payment.Purpose.HOT_LEAD,
        amount_usd=Decimal("0.20"), related_lead=hot_lead,
    )
    payment.confirm()
    payment.confirm()  # second call should not double-increment
    driver_user.refresh_from_db()
    assert driver_user.leads_used_this_month == 1


def test_second_driver_cannot_unlock_already_unlocked_lead(driver_user, second_driver, hot_lead):
    first_payment = Payment.objects.create(
        driver=driver_user, purpose=Payment.Purpose.HOT_LEAD,
        amount_usd=Decimal("0.20"), related_lead=hot_lead,
    )
    first_payment.confirm()
    hot_lead.refresh_from_db()
    assert hot_lead.is_open_for_unlock() is False

    # A second driver's payment for the same (already unlocked) lead should
    # not re-assign it — confirm() only acts when the lead is still OPEN.
    second_payment = Payment.objects.create(
        driver=second_driver, purpose=Payment.Purpose.HOT_LEAD,
        amount_usd=Decimal("0.20"), related_lead=hot_lead,
    )
    second_payment.confirm()
    hot_lead.refresh_from_db()
    assert hot_lead.unlocked_by == driver_user


def test_payment_confirm_extends_pro_weekly(driver_user):
    assert driver_user.is_pro is False
    payment = Payment.objects.create(
        driver=driver_user, purpose=Payment.Purpose.PRO_WEEKLY, amount_usd=Decimal("3.00"),
    )
    payment.confirm()
    driver_user.refresh_from_db()
    assert driver_user.is_pro is True
    days_left = (driver_user.pro_until - timezone.now()).days
    assert 6 <= days_left <= 7


def test_payment_confirm_stacks_pro_monthly_on_existing_pro(driver_user):
    driver_user.pro_until = timezone.now() + timezone.timedelta(days=5)
    driver_user.save()
    payment = Payment.objects.create(
        driver=driver_user, purpose=Payment.Purpose.PRO_MONTHLY, amount_usd=Decimal("10.00"),
    )
    payment.confirm()
    driver_user.refresh_from_db()
    days_left = (driver_user.pro_until - timezone.now()).days
    assert 33 <= days_left <= 35  # 5 existing + 30 new, roughly
