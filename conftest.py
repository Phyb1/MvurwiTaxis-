from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from taxis.models import Driver, Fare, Lead

# No collectstatic fixture needed: tests run under mvurwitaxis.settings.dev
# (see pytest.ini), which uses plain StaticFilesStorage — no manifest file
# required, so {% static %} tags in templates resolve without a pre-test
# collectstatic step. Production (settings.prod) still uses WhiteNoise's
# manifest storage; run collectstatic as part of deployment, not testing.


@pytest.fixture
def driver_user(db):
    user = User.objects.create_user(username="263775111111", password="testpass123")
    driver = Driver.objects.create(
        user=user,
        full_name="Tino Chapfika",
        phone_number="263775111111",
        car_type="hiace",
        car_reg="ADS1234",
        seats=8,
        base_area="Mvurwi Town",
        base_lat=-16.9333,
        base_lng=30.9333,
        routes="Harare, Bindura, NOC",
    )
    return driver


@pytest.fixture
def second_driver(db):
    user = User.objects.create_user(username="263775222222", password="testpass123")
    return Driver.objects.create(
        user=user,
        full_name="Kuda Moyo",
        phone_number="263775222222",
        car_type="corolla",
        car_reg="ABC9999",
        seats=4,
    )


@pytest.fixture
def fare(db):
    return Fare.objects.create(origin="Mvurwi", destination="Harare", price_usd="8.00")


@pytest.fixture
def hot_lead(db):
    return Lead.objects.create(
        kind=Lead.Kind.HOT,
        passenger_name="Rudo",
        passenger_phone="263771234567",
        pickup="Mvurwi Town",
        destination="Harare",
        people=2,
        requested_time="Now",
    )


@pytest.fixture(autouse=True)
def _isolated_settings(settings):
    """Make every test independent of whatever is in the developer's .env:
    no real push, no real SMTP, no admin WhatsApp number, a known domain."""
    settings.PUSH_NOTIFICATIONS_ENABLED = False
    settings.WHATSAPP_ADMIN_NUMBER = ""
    settings.SITE_DOMAIN = "mvurwitaxis.test"
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture
def direct_lead(driver_user):
    """A message request from a passenger to driver_user specifically."""
    return Lead.objects.create(
        kind=Lead.Kind.DIRECT,
        target_driver=driver_user,
        passenger_name="Rudo",
        passenger_phone="263771234567",
        pickup="Mvurwi Town",
        destination="Harare",
        people=2,
        requested_time="Now",
        message="I have 2 bags",
    )


@pytest.fixture
def make_pro():
    def _make_pro(driver, days=5):
        driver.pro_until = timezone.now() + timedelta(days=days)
        driver.save(update_fields=["pro_until"])
        return driver
    return _make_pro


@pytest.fixture
def use_up_free_quota(settings):
    def _use_up(driver):
        driver.leads_used_this_month = settings.FREE_TIER_LEAD_CAP
        driver.save(update_fields=["leads_used_this_month"])
        return driver
    return _use_up


@pytest.fixture
def new_hot_lead(db):
    def _new(name="Rudo"):
        return Lead.objects.create(
            kind=Lead.Kind.HOT, passenger_name=name, passenger_phone="263771234567",
            pickup="Mvurwi Town", destination="Harare", people=1,
        )
    return _new
