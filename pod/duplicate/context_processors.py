"""Esup-Pod duplicate context processor."""

from django.conf import settings as django_settings

USE_DUPLICATE = getattr(django_settings, "USE_DUPLICATE", False)


def context_settings(request):
    """Return all context settings for duplicate app."""
    new_settings = {}
    new_settings["USE_DUPLICATE"] = USE_DUPLICATE
    return new_settings
