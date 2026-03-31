"""
Configuration package initialization.

Attempts to import local setting overrides from `django.settings_local`.
This allows developers to apply machine-specific configurations (e.g., secrets,
debug flags) without modifying tracked files. If the module is missing,
it gracefully proceeds with default settings.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from .django.settings_local import *  # noqa: F401, F403
except ImportError:
    logger.debug(
        "No local settings overrides found (django/settings_local.py). "
        "Proceeding with default settings."
    )

from .celery import app as celery_app  # noqa: E402

__all__ = ("celery_app",)
