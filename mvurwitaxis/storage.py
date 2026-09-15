"""
Custom static storage for production.

Django's default ManifestStaticFilesStorage (and WhiteNoise's manifest
variant) raise a hard ValueError for any {% static %} reference not found
in staticfiles.json — by design, to catch broken deploys loudly. In
practice that "loud" failure can take down completely unrelated pages: a
missing manifest entry for one file (stale collectstatic, a file added
after the last collectstatic run) breaks page rendering anywhere that
file is referenced — including templates/404.html and templates/500.html,
turning an ordinary 404 into a 500 (see the incident this was added for).

manifest_strict = False falls back to the unhashed filename instead of
raising, and logs a warning so the underlying problem (run collectstatic)
is still visible in logs/django.log — it just can't crash the whole site.
"""
import logging

from whitenoise.storage import CompressedManifestStaticFilesStorage

logger = logging.getLogger("taxis")


class LenientManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content, filename)
        except ValueError:
            logger.warning(
                "Static file '%s' is missing from the staticfiles manifest — "
                "serving unhashed. Run `python manage.py collectstatic` to fix.",
                name,
            )
            return name
