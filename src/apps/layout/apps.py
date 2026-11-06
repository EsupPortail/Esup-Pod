"""
Esup-Pod - Layout application configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LayoutAppConfig(AppConfig):
    """Configuration for the layout app."""

    name = "src.apps.layout"
    verbose_name = _("Layout")

    def ready(self):
        """Initialize the layout application."""
        pass
