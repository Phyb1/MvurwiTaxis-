"""Unlock + tab rules (taxis/services.py). The four outcomes, in order:
Pro -> free; free tier with quota left -> free; quota used -> added to the
tab; tab due -> blocked until settled."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from taxis import services
from taxis.models import Lead, Payment, TabEntry
from taxis.services import Unlock

pytestmark = pytest.mark.django_db

PRICE = Decimal("0.20")


def submit_settlement(driver, amount="0.20", status=Payment.Status.PENDING):
    return Payment.objects.create(
        driver=driver, purpose=Payment.Purpose.TAB_SETTLEMENT,
        method=Payment.Method.ECOCASH, amount_usd=Decimal(amount),
        ecocash_reference="EC-SETTLE", status=status,
    )


# --- who pays what ---

def test_pro_driver_unlocks_free_with_no_tab_entry(driver_user, hot_lead, make_pro):
    make_pro(driver_user)
    result = services.unlock_lead(hot_lead.id, driver_user)

    assert result.outcome == Unlock.PRO and result.ok
    assert result.charged == Decimal("0.00")
    hot_lead.refresh_from_db()
    assert hot_lead.status == Lead.Status.UNLOCKED
    assert hot_lead.unlocked_by == driver_user
    assert TabEntry.objects.count() == 0


def test_free_driver_with_quota_left_unlocks_free(driver_user, hot_lead, settings):
    result = services.unlock_lead(hot_lead.id, driver_user)

    assert result.outcome == Unlock.FREE_QUOTA and result.ok
    assert TabEntry.objects.count() == 0
    assert driver_user.leads_used_this_month == 1
    assert driver_user.free_leads_left() == settings.FREE_TIER_LEAD_CAP - 1


def test_free_driver_past_quota_is_charged_to_the_tab(driver_user, hot_lead, use_up_free_quota):
    use_up_free_quota(driver_user)
    result = services.unlock_lead(hot_lead.id, driver_user)

    assert result.outcome == Unlock.ON_TAB and result.ok
    assert result.charged == PRICE
    entry = TabEntry.objects.get()
    assert entry.driver == driver_user and entry.lead == hot_lead
    assert entry.amount_usd == PRICE
    assert services.tab_balance(driver_user) == PRICE
    hot_lead.refresh_from_db()
    assert hot_lead.status == Lead.Status.UNLOCKED


# --- when the tab falls due ---

def test_tab_due_at_limit_blocks_further_unlocks(
    driver_user, use_up_free_quota, new_hot_lead, settings,
):
    settings.TAB_LIMIT_USD = "0.40"
    use_up_free_quota(driver_user)

    assert services.unlock_lead(new_hot_lead().id, driver_user).outcome == Unlock.ON_TAB
    assert services.unlock_lead(new_hot_lead().id, driver_user).outcome == Unlock.ON_TAB
    assert services.tab_balance(driver_user) == Decimal("0.40")
    assert services.tab_is_due(driver_user) is True

    blocked_lead = new_hot_lead()
    result = services.unlock_lead(blocked_lead.id, driver_user)
    assert result.outcome == Unlock.TAB_DUE and not result.ok
    blocked_lead.refresh_from_db()
    assert blocked_lead.status == Lead.Status.OPEN          # not unlocked...
    assert TabEntry.objects.count() == 2                    # ...and not charged


def test_tab_due_when_oldest_entry_is_too_old(
    driver_user, use_up_free_quota, new_hot_lead, settings,
):
    use_up_free_quota(driver_user)
    services.unlock_lead(new_hot_lead().id, driver_user)
    assert services.tab_is_due(driver_user) is False        # $0.20 < $1.00 limit

    old = timezone.now() - timedelta(days=settings.TAB_MAX_DAYS + 1)
    TabEntry.objects.update(created_at=old)                  # bypass auto_now_add

    assert services.tab_is_due(driver_user) is True
    assert services.unlock_lead(new_hot_lead().id, driver_user).outcome == Unlock.TAB_DUE


def test_within_free_quota_a_due_tab_does_not_block(
    driver_user, hot_lead, settings,
):
    """Tab rules only apply once the free quota is gone."""
    settings.TAB_LIMIT_USD = "0.00"
    assert services.unlock_lead(hot_lead.id, driver_user).outcome == Unlock.FREE_QUOTA


# --- settlement ---

def test_pending_settlement_covers_only_entries_that_existed_when_submitted(
    driver_user, use_up_free_quota, new_hot_lead, settings,
):
    settings.TAB_LIMIT_USD = "0.20"
    use_up_free_quota(driver_user)
    services.unlock_lead(new_hot_lead().id, driver_user)
    assert services.tab_is_due(driver_user) is True

    submit_settlement(driver_user)
    assert services.tab_is_due(driver_user) is False        # covered while pending

    # ...so the driver can keep working, but a NEW charge is not covered.
    assert services.unlock_lead(new_hot_lead().id, driver_user).outcome == Unlock.ON_TAB
    assert services.tab_is_due(driver_user) is True
    assert services.unlock_lead(new_hot_lead().id, driver_user).outcome == Unlock.TAB_DUE


def test_confirming_settlement_settles_only_earlier_entries(
    driver_user, use_up_free_quota, new_hot_lead,
):
    use_up_free_quota(driver_user)
    first = new_hot_lead()
    services.unlock_lead(first.id, driver_user)
    payment = submit_settlement(driver_user)
    second = new_hot_lead()
    services.unlock_lead(second.id, driver_user)             # after submission

    payment.confirm()

    early = TabEntry.objects.get(lead=first)
    late = TabEntry.objects.get(lead=second)
    assert early.settled_by == payment
    assert late.settled_by is None
    assert services.tab_balance(driver_user) == PRICE
    assert payment.confirmed_at is not None


def test_rejected_settlement_puts_the_tab_back_in_play(
    driver_user, use_up_free_quota, new_hot_lead, settings,
):
    settings.TAB_LIMIT_USD = "0.20"
    use_up_free_quota(driver_user)
    services.unlock_lead(new_hot_lead().id, driver_user)
    payment = submit_settlement(driver_user)
    assert services.tab_is_due(driver_user) is False

    payment.status = Payment.Status.REJECTED
    payment.save()

    assert services.tab_is_due(driver_user) is True
    assert services.tab_balance(driver_user) == PRICE


def test_can_settle_only_with_a_balance_and_nothing_pending(
    driver_user, use_up_free_quota, new_hot_lead,
):
    assert services.can_settle(driver_user) is False         # nothing owed
    use_up_free_quota(driver_user)
    services.unlock_lead(new_hot_lead().id, driver_user)
    assert services.can_settle(driver_user) is True
    submit_settlement(driver_user)
    assert services.can_settle(driver_user) is False         # one already pending


def test_uncovered_balance_excludes_entries_under_a_pending_settlement(
    driver_user, use_up_free_quota, new_hot_lead,
):
    use_up_free_quota(driver_user)
    services.unlock_lead(new_hot_lead().id, driver_user)
    assert services.uncovered_balance(driver_user) == PRICE
    submit_settlement(driver_user)
    assert services.uncovered_balance(driver_user) == Decimal("0.00")
    assert services.tab_balance(driver_user) == PRICE        # still owed until confirmed


# --- who may unlock what ---

def test_second_driver_loses_the_race_and_is_not_charged(
    driver_user, second_driver, hot_lead, use_up_free_quota,
):
    use_up_free_quota(driver_user)
    use_up_free_quota(second_driver)

    assert services.unlock_lead(hot_lead.id, driver_user).outcome == Unlock.ON_TAB
    assert services.unlock_lead(hot_lead.id, second_driver).outcome == Unlock.TAKEN

    hot_lead.refresh_from_db()
    assert hot_lead.unlocked_by == driver_user
    assert TabEntry.objects.filter(driver=second_driver).count() == 0


def test_direct_request_can_only_be_unlocked_by_its_target(driver_user, second_driver, direct_lead):
    assert services.unlock_lead(direct_lead.id, second_driver).outcome == Unlock.NOT_ALLOWED
    direct_lead.refresh_from_db()
    assert direct_lead.status == Lead.Status.OPEN

    assert services.unlock_lead(direct_lead.id, driver_user).outcome == Unlock.FREE_QUOTA


def test_passive_and_unknown_leads_cannot_be_unlocked(driver_user, db):
    passive = Lead.objects.create(
        kind=Lead.Kind.PASSIVE, driver_profile_viewed=driver_user,
        passenger_name="", passenger_phone="", pickup="", destination="",
    )
    assert services.unlock_lead(passive.id, driver_user).outcome == Unlock.NOT_ALLOWED
    assert services.unlock_lead(999_999, driver_user).outcome == Unlock.NOT_ALLOWED


# --- declining ---

def test_only_the_target_can_decline_and_only_while_open(driver_user, second_driver, direct_lead, hot_lead):
    assert services.decline_direct_request(direct_lead.id, second_driver) is False
    assert services.decline_direct_request(hot_lead.id, driver_user) is False   # broadcast: n/a

    assert services.decline_direct_request(direct_lead.id, driver_user) is True
    direct_lead.refresh_from_db()
    assert direct_lead.status == Lead.Status.DECLINED

    assert services.decline_direct_request(direct_lead.id, driver_user) is False  # already answered


def test_declined_request_cannot_then_be_unlocked(driver_user, direct_lead):
    services.decline_direct_request(direct_lead.id, driver_user)
    assert services.unlock_lead(direct_lead.id, driver_user).outcome == Unlock.TAKEN


# --- notification wording ---

def test_describe_unlock_cost_matches_the_drivers_situation(
    driver_user, make_pro, use_up_free_quota,
):
    text = services.describe_unlock_cost(driver_user)
    assert "3 free leads" in text

    use_up_free_quota(driver_user)
    text = services.describe_unlock_cost(driver_user)
    assert "0.20" in text and "tab" in text

    make_pro(driver_user)
    assert "Pro" in services.describe_unlock_cost(driver_user)
