"""Email every driver who owes money on their tab a statement.

Meant for a weekly cron job (cPanel: python manage.py send_tab_reminders).
Drivers whose whole balance is already covered by a pending settlement are
skipped — nagging someone who has already paid and is waiting for the admin
to confirm it would just be noise.
"""
from django.core.management.base import BaseCommand

from taxis import services
from taxis.models import Driver, TabEntry
from taxis.utils.emails import send_tab_statement


class Command(BaseCommand):
    help = "Email a tab statement to every driver with an unsettled balance."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="List who would be emailed without sending anything.",
        )

    def handle(self, *args, **options):
        driver_ids = (
            TabEntry.objects.filter(settled_by__isnull=True)
            .values_list("driver_id", flat=True).distinct()
        )
        sent = skipped = 0
        for driver in Driver.objects.filter(pk__in=driver_ids).order_by("full_name"):
            if services.uncovered_balance(driver) <= 0:
                skipped += 1
                continue
            balance = services.tab_balance(driver)
            if options["dry_run"]:
                self.stdout.write(f"Would email {driver.full_name}: ${balance}")
                sent += 1
            elif send_tab_statement(driver, balance):
                sent += 1
            else:
                skipped += 1  # no email on file, or the send failed (logged)
        verb = "Would send" if options["dry_run"] else "Sent"
        self.stdout.write(self.style.SUCCESS(f"{verb} {sent} statement(s); skipped {skipped}."))
