from taxis.utils.geo import haversine_km


def test_haversine_zero_distance_for_same_point():
    assert haversine_km(-16.9333, 30.9333, -16.9333, 30.9333) == 0.0


def test_haversine_mvurwi_to_harare_approx():
    # Mvurwi to Harare is roughly 90-100km as the crow flies.
    distance = haversine_km(-16.9333, 30.9333, -17.8292, 31.0522)
    assert 85 <= distance <= 110


def test_haversine_returns_none_for_missing_coords():
    assert haversine_km(None, 30.9, -17.8, 31.0) is None
    assert haversine_km(-16.9, None, -17.8, 31.0) is None
