"""Esup-Pod AI Enhancement apps."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IaEnhancementConfig(AppConfig):
    """AI Enhancement app configuration."""

    name = "pod.ai_enhancement"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Artificial Intelligence Enhancement")
