#!/usr/bin/env python
import os
import sys


def main():
    # manage.py is a local/dev tool — default to dev settings. Production
    # entry points (wsgi.py, passenger_wsgi.py) default to prod instead.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mvurwitaxis.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
