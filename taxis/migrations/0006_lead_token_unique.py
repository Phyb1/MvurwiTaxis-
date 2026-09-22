import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taxis", "0005_populate_lead_tokens"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lead",
            name="token",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                help_text="Private key for the passenger's status link, so the lead id is never exposed in URLs.",
                unique=True,
            ),
        ),
    ]
