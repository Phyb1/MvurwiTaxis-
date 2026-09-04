"""
Django settings for MvurwiTaxis.
Follows PHYB conventions: env-driven config, explicit static/media routes,
STORAGES dict (not deprecated STATICFILES_STORAGE), WhiteNoise for cPanel/Passenger.
"""
from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
SITE_DOMAIN = env("SITE_DOMAIN", default="localhost")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "taxis",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mvurwitaxis.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "mvurwitaxis.wsgi.application"

# SQLite by design — matches PHYB shared-hosting convention, sufficient at
# Mvurwi driver-volume scale. busy_timeout guards against concurrent writes
# during lead-unlock and payment confirmation races.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
            "init_command": "PRAGMA busy_timeout=20000;",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

# --- Static & media: explicit, matches PHYB debug checklist for Passenger 404s ---
STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "taxis:driver_login"
LOGIN_REDIRECT_URL = "taxis:driver_dashboard"
LOGOUT_REDIRECT_URL = "taxis:home"

# --- Business config ---
ECOCASH_MERCHANT_NUMBER = env("ECOCASH_MERCHANT_NUMBER", default="")
PAYNOW_INTEGRATION_ID = env("PAYNOW_INTEGRATION_ID", default="")
PAYNOW_INTEGRATION_KEY = env("PAYNOW_INTEGRATION_KEY", default="")
PAYNOW_RETURN_URL = env("PAYNOW_RETURN_URL", default="")
PAYNOW_RESULT_URL = env("PAYNOW_RESULT_URL", default="")
WHATSAPP_ADMIN_NUMBER = env("WHATSAPP_ADMIN_NUMBER", default="")

HOT_LEAD_PRICE_USD = "0.20"
PRO_WEEKLY_PRICE_USD = "3.00"
PRO_MONTHLY_PRICE_USD = "10.00"
GOING_TO_PIN_PRICE_USD = "0.50"
FREE_TIER_LEAD_CAP = 3
FREE_TIER_GOING_TO_CAP = 1
ONLINE_STATUS_WINDOW_MINUTES = 30

# --- Logging: auto-create logs/ dir, per PHYB pattern ---
(BASE_DIR / "logs").mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
        },
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
        "taxis": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
    },
}
