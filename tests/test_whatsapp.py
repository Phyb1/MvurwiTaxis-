from taxis.utils.whatsapp import build_wa_link, hail_message, normalize_phone, share_profile_message


def test_normalize_phone_strips_leading_zero():
    assert normalize_phone("0775123456") == "263775123456"


def test_normalize_phone_handles_plus_and_spaces():
    assert normalize_phone("+263 77 512 3456") == "263775123456"


def test_normalize_phone_already_normalized():
    assert normalize_phone("263775123456") == "263775123456"


def test_build_wa_link_no_message():
    link = build_wa_link("0775123456")
    assert link == "https://wa.me/263775123456"


def test_build_wa_link_with_message_is_url_encoded():
    link = build_wa_link("0775123456", "Hi there")
    assert link.startswith("https://wa.me/263775123456?text=")
    assert "Hi" in link and "%20" in link


def test_build_wa_link_empty_number_returns_empty_string():
    assert build_wa_link("") == ""


def test_hail_message_includes_destination():
    msg = hail_message("Harare", pickup="Mvurwi Town")
    assert "Harare" in msg
    assert "Mvurwi Town" in msg


def test_share_profile_message_includes_url():
    msg = share_profile_message("https://mvurwitaxis.co.zw/d/tino-ads1234")
    assert "https://mvurwitaxis.co.zw/d/tino-ads1234" in msg
