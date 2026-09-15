"""
Shared settings for MvurwiTaxis. Never import this directly for
DJANGO_SETTINGS_MODULE — use settings.dev or settings.prod, which both
import * from here and then override what differs.
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="dev-only-insecure-key")
SITE_DOMAIN = env("SITE_DOMAIN", default="localhost")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django.contrib.sitemaps",
    "crispy_forms",
    "crispy_bootstrap5",
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

# SQLite by design — matches shared-hosting reality; distance filtering uses
# plain haversine (taxis/utils/geo.py) instead of PostGIS. busy_timeout
# guards concurrent writes during lead-unlock/payment races.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {"timeout": 20, "init_command": "PRAGMA busy_timeout=20000;"},
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

STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "taxis:driver_login"
LOGIN_REDIRECT_URL = "taxis:driver_dashboard"
LOGOUT_REDIRECT_URL = "taxis:home"

# --- Business config ---
ECOCASH_MERCHANT_NUMBER = env("ECOCASH_MERCHANT_NUMBER", default="")
ECOCASH_MERCHANT_NAME = env("ECOCASH_MERCHANT_NAME", default="Phibeon Mazhuwa")
PAYNOW_INTEGRATION_ID = env("PAYNOW_INTEGRATION_ID", default="")
PAYNOW_INTEGRATION_KEY = env("PAYNOW_INTEGRATION_KEY", default="")
PAYNOW_RETURN_URL = env("PAYNOW_RETURN_URL", default="")
PAYNOW_RESULT_URL = env("PAYNOW_RESULT_URL", default="")
PAYNOW_ENABLED = env.bool("PAYNOW_ENABLED", default=False)
WHATSAPP_ADMIN_NUMBER = env("WHATSAPP_ADMIN_NUMBER", default="")

# --- Web Push (VAPID) ---
# Generate your OWN keypair with `python manage.py generate_vapid_keys` —
# never reuse a keypair from anywhere else, including any example/demo one.
VAPID_PUBLIC_KEY = env("VAPID_PUBLIC_KEY", default="")
VAPID_PRIVATE_KEY = env("VAPID_PRIVATE_KEY", default="")
VAPID_CLAIM_EMAIL = env("VAPID_CLAIM_EMAIL", default="mailto:admin@mvurwitaxis.co.zw")
PUSH_NOTIFICATIONS_ENABLED = bool(env("VAPID_PUBLIC_KEY", default="") and env("VAPID_PRIVATE_KEY", default=""))


HOT_LEAD_PRICE_USD = "0.20"
PRO_WEEKLY_PRICE_USD = "3.00"
PRO_MONTHLY_PRICE_USD = "10.00"
GOING_TO_PIN_PRICE_USD = "0.50"
FREE_TIER_LEAD_CAP = 3
FREE_TIER_GOING_TO_CAP = 1
ONLINE_STATUS_WINDOW_MINUTES = 30
# Pro drivers already pay a subscription, so hot leads are bundled in free
# for them — no per-lead EcoCash step. This is the main lever for cutting
# manual admin confirmation volume: it only ever remains on free-tier leads
# and Pro sign-ups themselves.
PRO_LEADS_BUNDLED_FREE = True

# --- Email (used for password reset + pro-driver lead notifications) ---
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@mvurwitaxis.co.zw")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# --- Logging ---
(BASE_DIR / "logs").mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {"class": "logging.FileHandler", "filename": BASE_DIR / "logs" / "django.log"},
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["file", "console"], "level": "ERROR", "propagate": False},
        "taxis": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
    },
}

# --- Third-party form styling ---
CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap5",)
CRISPY_TEMPLATE_PACK = "bootstrap5"
