"""
Esup-Pod - Live application configuration.
"""

from django.apps import AppConfig


class LiveConfig(AppConfig):
    """Configuration for the live app."""

    name = "src.apps.live"
    label = "live"
    verbose_name = "Live Streaming"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """Connect signals on app startup."""
        import src.apps.live.signals  # noqa: F401
