"""Esup-Pod dressing context processor."""

from django.conf import settings as django_settings

USE_DRESSING = getattr(django_settings, "USE_DRESSING", False)


def context_settings(request):
    """Return all context settings for dressing app."""
    new_settings = {}
    new_settings["USE_DRESSING"] = USE_DRESSING
    return new_settings
