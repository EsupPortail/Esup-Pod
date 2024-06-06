"""Esup-Pod context processors for speaker app."""

from django.conf import settings as django_settings

USE_SPEAKER = getattr(django_settings, "USE_SPEAKER", False)


def context_settings(request):
    """Return all context settings for speaker app."""
    new_settings = {}
    new_settings["USE_SPEAKER"] = USE_SPEAKER
    return new_settings
