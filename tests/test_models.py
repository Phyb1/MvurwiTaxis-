from datetime import timedelta

import pytest
from django.utils import timezone

from taxis.models import Driver, GoingToPost


def test_driver_slug_auto_generated(driver_user):
    assert driver_user.slug
    assert "tino" in driver_user.slug.lower()


def test_driver_slug_unique_on_collision(db, driver_user):
    from django.contrib.auth.models import User

    user2 = User.objects.create_user(username="263775999999", password="testpass123")
    dupe = Driver.objects.create(
        user=user2,
        full_name="Tino Chapfika",
        phone_number="263775999999",
        car_type="hiace",
        car_reg="ADS1234",  # same name+reg as driver_user fixture
    )
    assert dupe.slug != driver_user.slug


def test_is_pro_false_when_pro_until_none(driver_user):
    assert driver_user.is_pro is False


def test_is_pro_true_when_pro_until_future(driver_user):
    driver_user.pro_until = timezone.now() + timedelta(days=3)
    driver_user.save()
    assert driver_user.is_pro is True


def test_is_pro_false_when_pro_until_past(driver_user):
    driver_user.pro_until = timezone.now() - timedelta(days=1)
    driver_user.save()
    assert driver_user.is_pro is False


def test_is_online_false_when_never_online(driver_user):
    assert driver_user.is_online is False


def test_is_online_true_within_window(driver_user):
    driver_user.last_online_at = timezone.now() - timedelta(minutes=5)
    driver_user.save()
    assert driver_user.is_online is True


def test_is_online_false_outside_window(driver_user):
    driver_user.last_online_at = timezone.now() - timedelta(minutes=45)
    driver_user.save()
    assert driver_user.is_online is False


def test_free_tier_lead_cap_reached(driver_user):
    driver_user.leads_used_this_month = 3
    driver_user.save()
    assert driver_user.monthly_lead_cap_reached() is True


def test_free_tier_lead_cap_not_reached_below_limit(driver_user):
    driver_user.leads_used_this_month = 2
    driver_user.save()
    assert driver_user.monthly_lead_cap_reached() is False


def test_pro_driver_never_hits_lead_cap(driver_user):
    driver_user.leads_used_this_month = 99
    driver_user.pro_until = timezone.now() + timedelta(days=1)
    driver_user.save()
    assert driver_user.monthly_lead_cap_reached() is False


def test_going_to_post_default_expiry_24h(driver_user):
    post = GoingToPost.objects.create(
        driver=driver_user, destination="Harare", seats_available=4,
        price_usd="8.00", departure_text="2pm today",
    )
    delta = post.expires_at - post.created_at
    assert timedelta(hours=23, minutes=59) < delta < timedelta(hours=24, minutes=1)
    assert post.is_live is True


def test_going_to_post_not_live_after_expiry(driver_user):
    post = GoingToPost.objects.create(
        driver=driver_user, destination="Harare", seats_available=4,
        price_usd="8.00", departure_text="2pm today",
        expires_at=timezone.now() - timedelta(hours=1),
    )
    assert post.is_live is False


def test_distance_km_from_returns_none_without_coords(second_driver):
    assert second_driver.distance_km_from(-16.9, 30.9) is None


def test_distance_km_from_computes_with_coords(driver_user):
    distance = driver_user.distance_km_from(-17.8292, 31.0522)
    assert distance is not None
    assert distance > 0
