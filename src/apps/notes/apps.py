"""
Esup-Pod - Notes application configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NotesConfig(AppConfig):
    """Notes app configuration."""

    name = "src.apps.notes"
    verbose_name = _("Notes")
