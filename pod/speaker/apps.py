"""Esup-Pod speaker app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SpeakerConfig(AppConfig):
    """Speaker config app."""

    name = "pod.speaker"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Speaker")
