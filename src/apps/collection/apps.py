"""
Esup-Pod - Collection application configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CollectionAppConfig(AppConfig):
    """Configuration for the collection app."""

    name = "src.apps.collection"
    verbose_name = _("Collections")

    def ready(self):
        """Initialize the collection application."""
        pass
