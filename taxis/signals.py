"""
Lead-notification signal. Cuts manual involvement two ways:
1. Pro drivers are emailed the instant a hot lead is created — they don't
   have to keep the dashboard open and refresh it.
2. Pro drivers claim leads for free (see Driver.PRO_LEADS_BUNDLED_FREE /
   views.claim_lead_pro) — no EcoCash proof-of-payment step, so admin
   never has to confirm a payment for a lead a Pro driver takes.
Free-tier drivers still go through manual EcoCash confirmation, since
there's no live payment-gateway API wired up yet (see README "not built
yet"). That's the only place admin involvement remains.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from taxis.models import Driver, Lead
from taxis.utils.push import send_push

logger = logging.getLogger("taxis")


@receiver(post_save, sender=Lead)
def notify_pro_drivers_of_new_hot_lead(sender, instance, created, **kwargs):
    if not created or instance.kind != Lead.Kind.HOT:
        return

    pro_drivers = Driver.objects.filter(
        pro_until__gt=timezone.now(), is_active_listing=True,
    ).prefetch_related("push_subscriptions")

    if not pro_drivers.exists():
        return

    subject = f"New hot lead: {instance.pickup} -> {instance.destination}"
    body = (
        f"A passenger needs a taxi from {instance.pickup} to {instance.destination} "
        f"({instance.people} people, {instance.requested_time or 'time not given'}).\n\n"
        f"As a Pro driver you can claim it for free from your dashboard — "
        f"first to claim gets the passenger's number.\n"
        f"{settings.SITE_DOMAIN}"
    )
    recipients_with_email = [d for d in pro_drivers if d.email]
    if recipients_with_email:
        try:
            send_mail(
                subject, body, settings.DEFAULT_FROM_EMAIL,
                [d.email for d in recipients_with_email], fail_silently=False,
            )
        except Exception:
            # Never let a notification failure break lead creation for the
            # passenger — log it and move on.
            logger.exception("Failed to send hot-lead notification email to pro drivers")

    if settings.PUSH_NOTIFICATIONS_ENABLED:
        push_body = f"{instance.pickup} -> {instance.destination}, {instance.people} people. Tap to claim."
        for driver in pro_drivers:
            for subscription in driver.push_subscriptions.all():
                send_push(subscription, title="New hot lead", body=push_body, url="/dashboard/")
