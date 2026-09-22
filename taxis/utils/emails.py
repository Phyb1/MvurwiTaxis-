"""Transactional emails to drivers other than lead alerts (those live in
signals.py): the welcome/onboarding message and the tab statement.

Rendering happens inside the same try/except as sending, so a template
mistake can never turn a successful signup into a 500."""
import logging

from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

from taxis.services import lead_price, tab_limit
from taxis.utils.notify import absolute_url, send_email_safely
from taxis.utils.whatsapp import admin_help_message, build_wa_link

logger = logging.getLogger("taxis")


def _base_context(driver):
    return {
        "driver": driver,
        "dashboard_url": absolute_url(reverse("taxis:driver_dashboard")),
        "login_url": absolute_url(reverse("taxis:driver_login")),
        "profile_url": absolute_url(reverse("taxis:driver_profile", args=[driver.slug])),
        "tab_url": absolute_url(reverse("taxis:tab")),
        "free_cap": settings.FREE_TIER_LEAD_CAP,
        "lead_price": lead_price(),
        "tab_limit": tab_limit(),
        "tab_max_days": settings.TAB_MAX_DAYS,
        "online_window": settings.ONLINE_STATUS_WINDOW_MINUTES,
        "pro_weekly": settings.PRO_WEEKLY_PRICE_USD,
        "pro_monthly": settings.PRO_MONTHLY_PRICE_USD,
        "admin_wa_link": build_wa_link(settings.WHATSAPP_ADMIN_NUMBER, admin_help_message()),
    }


def _render_and_send(subject, template_name, context, recipient) -> bool:
    try:
        body = render_to_string(template_name, context)
    except Exception:
        logger.exception("Could not render %s for %s", template_name, recipient)
        return False
    return send_email_safely(subject, body, recipient)


def send_welcome_email(driver) -> bool:
    if not driver.email:
        return False
    return _render_and_send(
        "Welcome to MvurwiTaxis - 6 quick steps to your first passengers",
        "emails/driver_welcome.txt", _base_context(driver), driver.email,
    )


def send_tab_statement(driver, balance) -> bool:
    if not driver.email:
        return False
    context = _base_context(driver)
    context["balance"] = balance
    context["entries"] = list(driver.tab_entries.filter(settled_by__isnull=True))
    return _render_and_send(
        f"Your MvurwiTaxis tab: ${balance} to settle",
        "emails/tab_statement.txt", context, driver.email,
    )
