"""Apps for the Import_video module."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ImportVideoConfig(AppConfig):
    """Import video config.

    Args:
        AppConfig (Config): Config
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "pod.import_video"
    verbose_name = _("Import External Video")
