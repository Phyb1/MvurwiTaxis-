"""
Lead notifications. Two flows:

1. HOT ("Request Any Taxi"): Pro drivers are alerted the instant it's created
   and can unlock it for free from the dashboard — no need to keep the page
   open and refresh it.
2. DIRECT (passenger messaged ONE driver): that driver is alerted by push +
   email regardless of tier. The alert carries the passenger's name, route
   and message but never their phone number — the number is only revealed
   by unlocking (see taxis/services.py for the cost rules).

Alerts are best-effort: notify_driver() swallows and logs failures so a dead
SMTP server or stale push subscription can't break the passenger's request.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from taxis.models import Driver, Lead
from taxis.services import describe_unlock_cost
from taxis.utils.notify import absolute_url, notify_driver


@receiver(post_save, sender=Lead)
def notify_on_new_lead(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.kind == Lead.Kind.HOT:
        _notify_pro_drivers_of_hot_lead(instance)
    elif instance.kind == Lead.Kind.DIRECT:
        _notify_target_driver(instance)


def _notify_pro_drivers_of_hot_lead(lead):
    pro_drivers = Driver.objects.filter(
        pro_until__gt=timezone.now(), is_active_listing=True,
    ).prefetch_related("push_subscriptions")

    subject = f"New hot lead: {lead.pickup} -> {lead.destination}"
    body = (
        f"{lead.passenger_name} needs a taxi from {lead.pickup} to {lead.destination} "
        f"({lead.people} people, {lead.requested_time or 'time not given'}).\n\n"
        f"As a Pro driver you can unlock it for free from your dashboard - "
        f"first to unlock gets the passenger's number.\n"
        f"{absolute_url('/dashboard/')}"
    )
    push_body = f"{lead.pickup} -> {lead.destination}, {lead.people} people. Tap to unlock."
    for driver in pro_drivers:
        notify_driver(
            driver, subject=subject, body=body,
            push_title="New hot lead", push_body=push_body,
        )


def _notify_target_driver(lead):
    driver = lead.target_driver
    if driver is None:
        return

    lines = [
        f"{lead.passenger_name} sent you a request on MvurwiTaxis.",
        "",
        f"From: {lead.pickup}",
        f"To: {lead.destination}",
        f"People: {lead.people}",
        f"When: {lead.requested_time or 'not given'}",
    ]
    if lead.message:
        lines.append(f"Message: {lead.message}")
    lines += [
        "",
        describe_unlock_cost(driver),
        f"Open your dashboard to see their number and reply: {absolute_url('/dashboard/')}",
    ]
    notify_driver(
        driver,
        subject=f"New request from {lead.passenger_name}: {lead.pickup} -> {lead.destination}",
        body="\n".join(lines),
        push_title=f"Request from {lead.passenger_name}",
        push_body=f"{lead.pickup} -> {lead.destination}, {lead.people} people. Tap to open.",
    )
