"""Business rules for unlocking leads and the driver tab.

Views stay thin and call into here, so every rule below is unit-testable
without a request/response cycle (see tests/test_services.py).

Unlock rules, in the order they're applied:
  1. Pro driver                       -> number shown, free.
  2. Free tier, free quota left       -> number shown, uses one free lead.
  3. Free tier, quota used, tab OK    -> number shown, fee added to the tab.
  4. Free tier, quota used, tab due   -> blocked until the tab is settled.
The tab falls due at TAB_LIMIT_USD or after TAB_MAX_DAYS, whichever is first.
A settlement payment that's still awaiting admin confirmation "covers" the
entries that existed when it was submitted, so the driver isn't locked out
while the admin catches up — but only for those entries.
"""
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from taxis.models import Driver, Lead, Payment, TabEntry

ZERO = Decimal("0.00")


class Unlock:
    """Outcome codes returned by unlock_lead()."""

    PRO = "pro"
    FREE_QUOTA = "free_quota"
    ON_TAB = "on_tab"
    TAB_DUE = "tab_due"
    TAKEN = "taken"
    NOT_ALLOWED = "not_allowed"

    SUCCESS = frozenset({PRO, FREE_QUOTA, ON_TAB})


@dataclass(frozen=True)
class UnlockResult:
    outcome: str
    charged: Decimal = ZERO

    @property
    def ok(self):
        return self.outcome in Unlock.SUCCESS


# --- Prices & limits (read at call time so override_settings works in tests) ---

def lead_price() -> Decimal:
    return Decimal(settings.HOT_LEAD_PRICE_USD)


def tab_limit() -> Decimal:
    return Decimal(settings.TAB_LIMIT_USD)


# --- Tab queries ---

def _total(entries) -> Decimal:
    return entries.aggregate(total=Sum("amount_usd"))["total"] or ZERO


def unsettled_entries(driver):
    return TabEntry.objects.filter(driver=driver, settled_by__isnull=True)


def tab_balance(driver) -> Decimal:
    """Everything the driver currently owes."""
    return _total(unsettled_entries(driver))


def pending_settlement(driver):
    """The driver's newest settlement payment still awaiting confirmation, if any."""
    return (
        Payment.objects.filter(
            driver=driver,
            purpose=Payment.Purpose.TAB_SETTLEMENT,
            status=Payment.Status.PENDING,
        )
        .order_by("-created_at")
        .first()
    )


def uncovered_entries(driver):
    """Unsettled entries NOT already covered by a pending settlement payment."""
    entries = unsettled_entries(driver)
    pending = pending_settlement(driver)
    if pending is not None:
        entries = entries.filter(created_at__gt=pending.created_at)
    return entries


def uncovered_balance(driver) -> Decimal:
    """What the driver owes that no pending settlement already covers."""
    return _total(uncovered_entries(driver))


def tab_is_due(driver) -> bool:
    entries = uncovered_entries(driver)
    if _total(entries) >= tab_limit():
        return True
    oldest = entries.order_by("created_at").first()
    if oldest is None:
        return False
    return timezone.now() - oldest.created_at >= timedelta(days=settings.TAB_MAX_DAYS)


def can_settle(driver) -> bool:
    """A settlement can be submitted when there's a balance and none is pending."""
    return tab_balance(driver) > ZERO and pending_settlement(driver) is None


# --- Unlock / decline ---

def _may_unlock(lead, driver) -> bool:
    if lead.kind == Lead.Kind.HOT:
        return True  # broadcast: any driver may try; first one wins
    if lead.kind == Lead.Kind.DIRECT:
        return lead.target_driver_id == driver.pk
    return False  # passive leads carry no passenger data


def unlock_lead(lead_id, driver) -> UnlockResult:
    lead = Lead.objects.filter(pk=lead_id).first()
    if lead is None or not _may_unlock(lead, driver):
        return UnlockResult(Unlock.NOT_ALLOWED)
    if lead.status != Lead.Status.OPEN:
        return UnlockResult(Unlock.TAKEN)

    outcome, charge = Unlock.PRO, ZERO
    if not driver.is_pro:
        if not driver.monthly_lead_cap_reached():
            outcome = Unlock.FREE_QUOTA
        elif tab_is_due(driver):
            return UnlockResult(Unlock.TAB_DUE)
        else:
            outcome, charge = Unlock.ON_TAB, lead_price()

    with transaction.atomic():
        # Conditional UPDATE: if two drivers race for a broadcast lead, only
        # one row update succeeds — the loser gets TAKEN and is never charged.
        claimed = Lead.objects.filter(pk=lead.pk, status=Lead.Status.OPEN).update(
            status=Lead.Status.UNLOCKED, unlocked_by=driver, unlocked_at=timezone.now(),
        )
        if not claimed:
            return UnlockResult(Unlock.TAKEN)
        if charge:
            TabEntry.objects.create(driver=driver, lead=lead, amount_usd=charge)
        Driver.objects.filter(pk=driver.pk).update(
            leads_used_this_month=F("leads_used_this_month") + 1
        )
    driver.refresh_from_db(fields=["leads_used_this_month"])
    return UnlockResult(outcome, charged=charge)


def decline_direct_request(lead_id, driver) -> bool:
    """Only the targeted driver can decline, and only while it's still open."""
    updated = Lead.objects.filter(
        pk=lead_id, kind=Lead.Kind.DIRECT, target_driver=driver, status=Lead.Status.OPEN,
    ).update(status=Lead.Status.DECLINED)
    return bool(updated)


def describe_unlock_cost(driver) -> str:
    """One sentence for notifications: what it costs THIS driver to see the number."""
    if driver.is_pro:
        return "As a Pro driver, showing the passenger's number is free."
    left = driver.free_leads_left()
    if left > 0:
        return f"You have {left} free lead{'s' if left != 1 else ''} left this month."
    return f"Showing the number adds ${lead_price()} to your tab."
