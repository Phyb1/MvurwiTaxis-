"""Thin wrapper around pywebpush. Every call is best-effort: a dead
subscription (driver uninstalled, cleared browser data) should never break
whatever triggered the notification — see taxis/signals.py, which is the
only current caller."""
import json
import logging

from django.conf import settings

logger = logging.getLogger("taxis")


def send_push(subscription, title, body, url="/"):
    """subscription: a PushSubscription instance. Returns True/False —
    callers should treat False as 'log and move on', never as fatal."""
    if not settings.PUSH_NOTIFICATIONS_ENABLED:
        return False

    from pywebpush import WebPushException, webpush

    payload = json.dumps({"title": title, "body": body, "url": url})

    try:
        webpush(
            subscription_info=subscription.as_subscription_info(),
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL},
        )
        return True
    except WebPushException as exc:
        # 404/410 means the subscription is dead (uninstalled, expired) —
        # clean it up so we stop trying. Anything else, just log it.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            subscription.delete()
        else:
            logger.warning("Push notification failed for %s: %s", subscription.driver, exc)
        return False
    except Exception:
        logger.exception("Unexpected error sending push notification to %s", subscription.driver)
        return False
