"""
Esup-Pod - Core application configuration.
"""

from django.apps import AppConfig
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    """
    AppConfig for the Core application, handles configuration loading.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.apps.core"
    verbose_name = "Core Configuration Management"

    def ready(self):
        """Checks for the existence of the configuration file upon app startup."""
        conf_path = os.path.join(
            settings.BASE_DIR, "src", "apps", "core", "configuration.json"
        )
        if not os.path.exists(conf_path):
            logger.warning(
                f"Configuration file missing at {conf_path}. Management commands won't work."
            )
