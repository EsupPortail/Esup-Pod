"""
Esup-Pod - Import Video application configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ImportVideoConfig(AppConfig):
    """Import Video app configuration."""

    name = "src.apps.import_video"
    verbose_name = _("Import Video")
