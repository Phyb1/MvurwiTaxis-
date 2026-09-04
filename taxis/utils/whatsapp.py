"""Shared WhatsApp link builder, matching the whatsapp.py utility pattern
used across other PHYB client projects (Hodha, Mimie's Closet, etc.)."""
from urllib.parse import quote

WA_BASE_URL = "https://wa.me/"


def normalize_phone(phone_number: str) -> str:
    """Strip spaces, +, and leading 0; expects/produces 263-prefixed digits."""
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    if digits.startswith("0"):
        digits = "263" + digits[1:]
    if not digits.startswith("263") and len(digits) == 9:
        digits = "263" + digits
    return digits


def build_wa_link(phone_number: str, message: str = "") -> str:
    """Build a wa.me deep link. Safe with no message (bare chat open)."""
    number = normalize_phone(phone_number)
    if not number:
        return ""
    url = f"{WA_BASE_URL}{number}"
    if message:
        url += f"?text={quote(message)}"
    return url


def hail_message(destination: str, pickup: str = "") -> str:
    pickup_part = f" from {pickup}" if pickup else ""
    return (
        f"Hi, I saw you on MvurwiTaxis. Need a taxi{pickup_part} to {destination}."
    )


def share_profile_message(profile_url: str) -> str:
    return f"Need a taxi in Mvurwi? Book me on MvurwiTaxis: {profile_url}. Available now."
