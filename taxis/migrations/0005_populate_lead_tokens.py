import uuid

from django.db import migrations


def fill_tokens(apps, schema_editor):
    Lead = apps.get_model("taxis", "Lead")
    # list(), not .iterator(): SQLite has no isolation between a read cursor
    # and writes on the same connection.
    for lead in list(Lead.objects.filter(token__isnull=True)):
        lead.token = uuid.uuid4()
        lead.save(update_fields=["token"])


class Migration(migrations.Migration):

    dependencies = [
        ("taxis", "0004_direct_requests_and_tab"),
    ]

    operations = [
        migrations.RunPython(fill_tokens, migrations.RunPython.noop),
    ]
