"""Best-effort email + Web Push to ONE driver. Every send is isolated so a
dead SMTP server or a stale push subscription never breaks the request that
triggered it (see taxis/signals.py)."""
import logging

from django.conf import settings
from django.core.mail import send_mail

from taxis.utils.push import send_push

logger = logging.getLogger("taxis")


def absolute_url(path: str = "/") -> str:
    """SITE_DOMAIN may be a bare domain ('mvurwitaxis.co.zw') or a full origin."""
    domain = settings.SITE_DOMAIN.rstrip("/")
    if not domain.startswith(("http://", "https://")):
        domain = f"https://{domain}"
    return f"{domain}{path}"


def send_email_safely(subject, body, recipient) -> bool:
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
        return True
    except Exception:
        logger.exception("Failed to send email %r to %s", subject, recipient)
        return False


def notify_driver(driver, *, subject, body, push_title, push_body, url="/dashboard/"):
    """Email (if the driver has an address) and push (to every subscribed
    device). One email per driver, so addresses are never shared between
    recipients. Returns (emailed: bool, pushes_sent: int) for callers/tests."""
    emailed = bool(driver.email) and send_email_safely(subject, body, driver.email)

    pushes_sent = 0
    if settings.PUSH_NOTIFICATIONS_ENABLED:
        for subscription in driver.push_subscriptions.all():
            if send_push(subscription, title=push_title, body=push_body, url=url):
                pushes_sent += 1
    return emailed, pushes_sent
