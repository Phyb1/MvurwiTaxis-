"""Production settings. DJANGO_SETTINGS_MODULE=mvurwitaxis.settings.prod
Used on the cPanel/Passenger deployment.
"""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["mvurwitaxis.co.zw", "www.mvurwitaxis.co.zw"])

# Django emails ADMINS on any unhandled 500 (via django.utils.log.AdminEmailHandler,
# wired automatically when DEBUG=False) — the closest thing to "robust error
# handling" that doesn't require a third-party error tracker.
ADMINS = [("Phibeon Mazhuwa", env("ADMIN_EMAIL", default=""))] if env("ADMIN_EMAIL", default="") else []
MANAGERS = ADMINS

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "mvurwitaxis.storage.LenientManifestStaticFilesStorage"},
}

# SMTP email — required for password reset + pro-driver lead notifications
# to actually deliver in production. Falls back to console backend if unset
# so a misconfigured deploy fails loudly in logs rather than 500ing.
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
if not EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = [
    "https://mvurwitaxis.co.zw",
    "https://www.mvurwitaxis.co.zw",
]

