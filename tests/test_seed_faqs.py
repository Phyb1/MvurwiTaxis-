"""python manage.py seed_faqs (taxis/management/commands/seed_faqs.py).

Idempotent by default so re-running it in production never clobbers an
admin's manual edits; --update-existing is the escape hatch for when the
seed copy itself changes (e.g. pricing, or describing a flow that no
longer exists) and existing rows need to actually pick that up."""
from decimal import Decimal

import pytest
from django.core.management import call_command

from taxis.models import FAQ

pytestmark = pytest.mark.django_db


def test_seed_faqs_creates_entries_for_both_audiences():
    call_command("seed_faqs")
    assert FAQ.objects.filter(audience=FAQ.Audience.PASSENGER).exists()
    assert FAQ.objects.filter(audience=FAQ.Audience.DRIVER).exists()


def test_seed_faqs_is_idempotent_by_default():
    call_command("seed_faqs")
    count = FAQ.objects.count()
    call_command("seed_faqs")
    assert FAQ.objects.count() == count


def test_seed_faqs_does_not_overwrite_an_admin_edited_answer_by_default():
    call_command("seed_faqs")
    faq = FAQ.objects.get(question="How do I go online/offline?")
    faq.answer = "Custom answer written by the admin."
    faq.save()

    call_command("seed_faqs")

    faq.refresh_from_db()
    assert faq.answer == "Custom answer written by the admin."


def test_seed_faqs_update_existing_overwrites_stale_answers():
    call_command("seed_faqs")
    faq = FAQ.objects.get(question="How do leads and unlocking work?")
    faq.answer = "Old description of the per-lead payment flow."
    faq.save()

    call_command("seed_faqs", "--update-existing")

    faq.refresh_from_db()
    assert faq.answer != "Old description of the per-lead payment flow."
    assert "tab" in faq.answer


def test_seeded_pricing_copy_matches_settings(settings):
    settings.FREE_TIER_LEAD_CAP = 5
    settings.HOT_LEAD_PRICE_USD = "0.30"
    call_command("seed_faqs")
    faq = FAQ.objects.get(question="How much does it cost to list my taxi?")
    assert "5 free leads" in faq.answer
