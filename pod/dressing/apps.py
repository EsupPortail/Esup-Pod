"""Esup-Pod dressing apps."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DressingConfig(AppConfig):
    """Video dressing config app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pod.dressing"
    verbose_name = _("Video dressings")
