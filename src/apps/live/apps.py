"""
Esup-Pod - Live application configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LiveConfig(AppConfig):
    """Configuration for the live app."""

    name = "src.apps.live"
    label = "live"
    verbose_name = _("Live Streaming")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """Connect signals on app startup."""
        import src.apps.live.signals  # noqa: F401
