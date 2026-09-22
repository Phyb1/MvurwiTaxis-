import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Schema half of the direct-request + tab feature.

    Lead.token is added nullable here; 0005 fills it for existing rows and
    0006 makes it unique. Three steps because adding a unique UUID with a
    callable default in one go would give every existing row the SAME value.
    """

    dependencies = [
        ("taxis", "0003_pushsubscription"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="message",
            field=models.CharField(
                blank=True,
                help_text="Optional note from the passenger to the driver.",
                max_length=300,
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="token",
            field=models.UUIDField(
                editable=False,
                help_text="Private key for the passenger's status link, so the lead id is never exposed in URLs.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="target_driver",
            field=models.ForeignKey(
                blank=True,
                help_text="Set only for direct requests a passenger sends to one specific driver.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="direct_requests",
                to="taxis.driver",
            ),
        ),
        migrations.AlterField(
            model_name="lead",
            name="kind",
            field=models.CharField(
                choices=[("passive", "Passive"), ("hot", "Hot"), ("direct", "Direct message")],
                default="hot",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="lead",
            name="status",
            field=models.CharField(
                choices=[
                    ("open", "Open"),
                    ("unlocked", "Unlocked"),
                    ("declined", "Declined"),
                    ("expired", "Expired"),
                ],
                default="open",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="purpose",
            field=models.CharField(
                choices=[
                    ("hot_lead", "Hot Lead Unlock"),
                    ("pro_weekly", "Pro Subscription (Weekly)"),
                    ("pro_monthly", "Pro Subscription (Monthly)"),
                    ("going_to_pin", "Going-To Pin"),
                    ("tab_settlement", "Tab Settlement"),
                ],
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="TabEntry",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount_usd", models.DecimalField(decimal_places=2, max_digits=6)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tab_entries",
                        to="taxis.driver",
                    ),
                ),
                (
                    "lead",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tab_entries",
                        to="taxis.lead",
                    ),
                ),
                (
                    "settled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="settled_tab_entries",
                        to="taxis.payment",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "tab entries",
                "ordering": ["-created_at"],
            },
        ),
    ]
