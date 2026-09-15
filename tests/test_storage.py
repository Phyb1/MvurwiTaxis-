from unittest import mock

from mvurwitaxis.storage import LenientManifestStaticFilesStorage


def test_hashed_name_falls_back_instead_of_raising(caplog):
    """Reproduces the incident this class exists for: a manifest entry
    missing for one file must not raise — it should serve the unhashed
    name and log a warning instead, so the rest of the page still renders."""
    storage = LenientManifestStaticFilesStorage.__new__(LenientManifestStaticFilesStorage)

    with mock.patch(
        "whitenoise.storage.CompressedManifestStaticFilesStorage.hashed_name",
        side_effect=ValueError("Missing staticfiles manifest entry for 'manifest.json'"),
    ):
        with caplog.at_level("WARNING", logger="taxis"):
            result = storage.hashed_name("manifest.json")

    assert result == "manifest.json"
    assert "manifest.json" in caplog.text
    assert "collectstatic" in caplog.text


def test_hashed_name_passes_through_on_success():
    storage = LenientManifestStaticFilesStorage.__new__(LenientManifestStaticFilesStorage)

    with mock.patch(
        "whitenoise.storage.CompressedManifestStaticFilesStorage.hashed_name",
        return_value="css/style.abc123.css",
    ):
        result = storage.hashed_name("css/style.css")

    assert result == "css/style.abc123.css"
