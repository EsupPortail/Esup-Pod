"""
Esup-Pod - ASGI configuration.

Exposes the ASGI callable as a module-level variable named ``application``.
Validates that `DJANGO_SETTINGS_MODULE` is correctly set before initializing
the application to ensure fail-fast behavior in misconfigured environments.
"""

import logging
import os
import sys

from django.core.asgi import get_asgi_application
from django.core.exceptions import ImproperlyConfigured

from config.env import env

logger = logging.getLogger(__name__)

try:
    settings_module = env.str("DJANGO_SETTINGS_MODULE")

    if not settings_module:
        raise ValueError("DJANGO_SETTINGS_MODULE is set but empty.")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    application = get_asgi_application()

except (ImproperlyConfigured, ImportError, ValueError) as e:
    logger.critical(
        "FATAL ERROR: Failed to initialize the ASGI application. "
        "Check that DJANGO_SETTINGS_MODULE is set. Details: %s",
        e,
        exc_info=True,
    )
    sys.exit(1)
