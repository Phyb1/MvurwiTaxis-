from django.conf import settings
from django.core.management.base import BaseCommand

from taxis.models import FAQ


def _build_faqs():
    """Built at call time (not import time) so pricing changes to settings
    are reflected without restarting whatever process imported this module.

    Prices/limits are pulled from settings rather than hardcoded so this
    stays correct if HOT_LEAD_PRICE_USD, FREE_TIER_LEAD_CAP etc. are ever
    tuned -- see the incident this avoids: the old copy still said "3
    leads/month" and described a pay-before-you-see-it flow after the tab
    model replaced it, until someone actually read the page again.
    """
    return [
        ("How do I book a taxi?",
         "Browse the directory and tap \"Message\" on a driver's card — it "
         "sends your trip details straight to them and they reply to you "
         "directly. You'll get a private link to follow the status. Prefer "
         "WhatsApp? Every profile has a WhatsApp button too.",
         FAQ.Audience.PASSENGER, 1),
        ("What happens after I message a driver?",
         "The driver gets an alert (notification and email) with your trip and "
         "any note you added — not your phone number, until they respond. "
         "Keep your status page open, or bookmark it; it updates itself, and "
         "offers you WhatsApp or another driver if they don't reply.",
         FAQ.Audience.PASSENGER, 2),
        ("What if no taxi is available near me, or I don't want to pick one?",
         "Use \"Request Any Taxi\" on the homepage — it's sent to every online "
         "driver, and the first to accept will contact you.",
         FAQ.Audience.PASSENGER, 3),
        ("Are the fares official?",
         "The Fares page is the reference price for each route, kept updated "
         "by MvurwiTaxis admin.",
         FAQ.Audience.PASSENGER, 4),
        ("Is it free for passengers?",
         "Yes, 100% free. Only drivers pay, and only past their monthly free "
         "leads.",
         FAQ.Audience.PASSENGER, 5),

        ("How much does it cost to list my taxi?",
         f"Free tier: $0, listed at the bottom, {settings.FREE_TIER_LEAD_CAP} "
         f"free leads/month. Pro: ${settings.PRO_WEEKLY_PRICE_USD}/week or "
         f"${settings.PRO_MONTHLY_PRICE_USD}/month for unlimited free unlocks "
         "and top placement.",
         FAQ.Audience.DRIVER, 10),
        ("How do leads and unlocking work?",
         f"When you tap to see a passenger's number: if you're Pro, or you "
         f"still have free leads this month, it's free. After that, "
         f"${settings.HOT_LEAD_PRICE_USD} is added to your tab instead of "
         "asking you to pay on the spot — no payment step in the moment, "
         "no waiting on admin confirmation before you can call the passenger.",
         FAQ.Audience.DRIVER, 11),
        ("What is my \"tab\"?",
         f"The running total of unlocks past your free quota. Settle it "
         f"whenever you like from your dashboard; it must be settled once it "
         f"reaches ${settings.TAB_LIMIT_USD} or is {settings.TAB_MAX_DAYS} "
         "days old, otherwise new unlocks pause until you do. You'll also get "
         "a weekly reminder email if you owe anything.",
         FAQ.Audience.DRIVER, 12),
        ("How do I pay?",
         "From your dashboard's Tab page: EcoCash to the number shown, then "
         "submit your reference or a screenshot. Paynow is available too "
         "where enabled. This is only for settling your tab or going Pro — "
         "unlocking a lead itself doesn't need payment upfront.",
         FAQ.Audience.DRIVER, 13),
        ("How long until my payment is confirmed?",
         "Tab settlements and Pro payments are confirmed by admin, usually "
         "within minutes during the day. You can keep unlocking leads while a "
         "settlement is pending.",
         FAQ.Audience.DRIVER, 14),
        ("Do I need an email address?",
         "Yes — it's how you get alerted the moment a passenger messages you, "
         "and how you'd reset your password if you forget it. If you signed "
         "up before this was required, add one from your dashboard.",
         FAQ.Audience.DRIVER, 15),
        ("How do notifications work?",
         "Tap \"Turn on request notifications\" on your dashboard to get a "
         "push alert the moment someone messages you or a hot lead opens — "
         "plus an email either way. On iPhone, first add MvurwiTaxis to your "
         "home screen (Share, then Add to Home Screen), then turn them on "
         "from there.",
         FAQ.Audience.DRIVER, 16),
        ("What does 'Verified' mean?",
         "Admin has checked your license and vehicle registration. Verified "
         "drivers are trusted more by passengers and rank higher.",
         FAQ.Audience.DRIVER, 17),
        ("How do I go online/offline?",
         f"Use the GO ONLINE button on your dashboard. You'll show as "
         f"\"Available now\" for {settings.ONLINE_STATUS_WINDOW_MINUTES} "
         "minutes, refreshed each time you open the dashboard.",
         FAQ.Audience.DRIVER, 18),
        ]


class Command(BaseCommand):
    help = "Seed starter FAQs for passengers and drivers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update-existing", action="store_true",
            help=(
                "Overwrite the answer/audience/order of any FAQ whose "
                "question already exists, instead of only adding new ones. "
                "Use after editing the copy above so a stale seeded answer "
                "(e.g. describing the old per-lead payment flow) actually "
                "gets replaced rather than silently skipped."
            ),
        )

    def handle(self, *args, **options):
        faqs = _build_faqs()
        created = updated = 0
        for question, answer, audience, order in faqs:
            obj, was_created = FAQ.objects.get_or_create(
                question=question,
                defaults={"answer": answer, "audience": audience, "order": order},
            )
            if was_created:
                created += 1
            elif options["update_existing"]:
                obj.answer, obj.audience, obj.order = answer, audience, order
                obj.save(update_fields=["answer", "audience", "order"])
                updated += 1
        skipped = len(faqs) - created - updated
        self.stdout.write(self.style.SUCCESS(
            f"Seeded {created} new FAQ(s), updated {updated}, skipped {skipped} unchanged/existing."
        ))
