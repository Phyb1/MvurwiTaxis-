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

# django-debug-toolbar refuses to render for hosts it doesn't recognise as
# "internal" unless SHOW_TOOLBAR_CALLBACK is relaxed — handy under Termux
# where localhost may resolve oddly.
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG}
