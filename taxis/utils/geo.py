"""Haversine distance helper. Used instead of PostGIS, which isn't
available on cPanel/shared-hosting Postgres/SQLite setups. Fine at
Mvurwi's town-sized service radius and driver volume."""
import math


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in kilometres between two lat/lng points."""
    if None in (lat1, lng1, lat2, lng2):
        return None
    r = 6371.0  # Earth radius, km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 2)
