"""
Entry point for cPanel Phusion Passenger. Mirrors the pattern used across
other PHYB deployments (mathxuco account, Passenger/LiteSpeed).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mvurwitaxis.settings.prod")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
