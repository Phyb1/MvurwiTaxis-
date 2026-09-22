"""Settings for the pytest process. DJANGO_SETTINGS_MODULE=mvurwitaxis.settings.test
Identical to dev except debug_toolbar is stripped out entirely — Django's
test runner overrides settings.DEBUG to False mid-session, which the
toolbar doesn't handle cleanly (see the note in dev.py). Simplest fix is
to just not install it for the test process; a toolbar was never useful
inside a test run anyway.
"""
from .dev import *  # noqa: F401,F403
from .dev import BASE_DIR, INSTALLED_APPS, LOGGING, MIDDLEWARE

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]
MIDDLEWARE = [mw for mw in MIDDLEWARE if "debug_toolbar" not in mw]

# The "taxis" logger sets propagate: False in base.py so production logs
# aren't duplicated between its own file/console handlers and root's. But
# pytest's caplog fixture only ever attaches to the root logger, so with
# propagate False a warning logged via logging.getLogger("taxis") -- e.g.
# LenientManifestStaticFilesStorage's fallback warning -- is invisible to
# caplog.at_level(...) even though it fires correctly. Copy the dict rather
# than mutate LOGGING in place, since dev.py's copy is the same object
# base.py built and other settings modules read from it too.
LOGGING = {
    **LOGGING,
    "loggers": {
        **LOGGING["loggers"],
        "taxis": {**LOGGING["loggers"]["taxis"], "propagate": True},
    },
}

# Tests that exercise ImageField uploads (compression tests) write real
# files — keep them out of the real media/ directory so repeated test runs
# don't accumulate junk there.
MEDIA_ROOT = BASE_DIR / "test-media"
