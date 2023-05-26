"""Esup-Pod Favorite video app."""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FavoriteConfig(AppConfig):
    """Favorite configuration app."""

    name = "pod.favorite"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Favorite videos")
