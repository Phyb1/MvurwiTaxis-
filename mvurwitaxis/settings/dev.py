"""Development settings. DJANGO_SETTINGS_MODULE=mvurwitaxis.settings.dev
Also used for tests (pytest.ini points here) — deliberately: tests should
run against the same "no collectstatic required" storage a developer gets
locally, not the production manifest storage.
"""
from .base import *  # noqa: F401,F403
from .base import env, BASE_DIR, INSTALLED_APPS, MIDDLEWARE

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Plain filesystem storage — no staticfiles.json manifest required, so
# templates using {% static %} work immediately without collectstatic.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
INTERNAL_IPS = ["127.0.0.1", "localhost"]
# Deliberately NOT setting a custom SHOW_TOOLBAR_CALLBACK here — the default
# (checks INTERNAL_IPS against settings.DEBUG live, every request) is safe.
# An earlier version used `lambda request: DEBUG`, closing over this
# module's DEBUG=True constant captured at import time — that silently kept
# returning True even when Django's test runner overrides settings.DEBUG to
# False for the test session, while urls.py's `if settings.DEBUG` guard
# (evaluated lazily, after that override) correctly excluded the djdt URLs.
# Result: middleware tried to render a toolbar whose URLs were never
# registered -> NoReverseMatch. Two different readings of "DEBUG" disagreeing.
# mvurwitaxis.settings.test (see test.py) sidesteps this entirely by not
# installing debug_toolbar for the test process at all.
