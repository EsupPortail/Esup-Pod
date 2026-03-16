"""
WSGI configuration.

Exposes the WSGI callable as a module-level variable named ``application``.
Validates that `DJANGO_SETTINGS_MODULE` is correctly set before initializing
the application to ensure fail-fast behavior in misconfigured environments.
"""
import os
import sys

from django.core.wsgi import get_wsgi_application
from django.core.exceptions import ImproperlyConfigured

from config.env import env

try:
    settings_module = env.str("DJANGO_SETTINGS_MODULE")

    if not settings_module:
        raise ValueError("DJANGO_SETTINGS_MODULE is set but empty.")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    application = get_wsgi_application()

except (ImproperlyConfigured, ImportError, ValueError) as e:
    print(
        f"FATAL ERROR: Failed to initialize the WSGI application. "
        f"Check that DJANGO_SETTINGS_MODULE is set. Details: {e}",
        file=sys.stderr,
    )
    sys.exit(1)
