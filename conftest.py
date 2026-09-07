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
