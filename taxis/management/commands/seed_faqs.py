from django.core.management.base import BaseCommand

from taxis.models import FAQ

FAQS = [
    ("How do I book a taxi?", "Browse the directory, tap WhatsApp on any driver's card, and message them directly. No account needed.", FAQ.Audience.PASSENGER, 1),
    ("What if no taxi is available near me?", "Use 'Request Any Taxi' on the homepage — it's sent to every online driver, and the first to accept will contact you.", FAQ.Audience.PASSENGER, 2),
    ("Are the fares official?", "The Fares page is the reference price for each route, kept updated by MvurwiTaxis admin.", FAQ.Audience.PASSENGER, 3),
    ("Is it free for passengers?", "Yes, 100% free. Only drivers pay, and only when they get a customer.", FAQ.Audience.PASSENGER, 4),

    ("How much does it cost to list my taxi?", "Free tier: $0, listed at the bottom, 3 leads/month. Pro: $3/week or $10/month for unlimited leads and top placement.", FAQ.Audience.DRIVER, 10),
    ("How do Hot Leads work?", "A passenger requests a taxi, we notify online drivers, and you pay a small fee to unlock their number — unless you're Pro, in which case claiming is free.", FAQ.Audience.DRIVER, 11),
    ("How do I pay?", "EcoCash to the number shown on the payment page, then submit your reference or a screenshot. Paynow is available too where enabled.", FAQ.Audience.DRIVER, 12),
    ("How long until my payment is confirmed?", "Free-tier lead payments are confirmed by admin, usually within minutes during the day. Pro drivers skip this step entirely — claims are instant.", FAQ.Audience.DRIVER, 13),
    ("What does 'Verified' mean?", "Admin has checked your license and vehicle registration. Verified drivers are trusted more by passengers and rank higher.", FAQ.Audience.DRIVER, 14),
    ("How do I go online/offline?", "Use the GO ONLINE button on your dashboard. You'll show as 'Available now' for 30 minutes, refreshed each time you open the dashboard.", FAQ.Audience.DRIVER, 15),
]


class Command(BaseCommand):
    help = "Seed starter FAQs for passengers and drivers (idempotent — skips existing questions)."

    def handle(self, *args, **options):
        created = 0
        for question, answer, audience, order in FAQS:
            _, was_created = FAQ.objects.get_or_create(
                question=question,
                defaults={"answer": answer, "audience": audience, "order": order},
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Seeded {created} new FAQ(s), {len(FAQS) - created} already existed."))
