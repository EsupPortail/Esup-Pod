"""
Esup-Pod - Dressing application configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DressingConfig(AppConfig):
    """
    AppConfig for the dressing app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.apps.dressing"
    verbose_name = _("Dressing")

    def ready(self):
        """Connects signals on app startup."""
        import src.apps.dressing.signals  # noqa: F401
