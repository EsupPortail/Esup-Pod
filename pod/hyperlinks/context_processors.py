"""Esup-Pod hyperlinks context processor."""

from django.conf import settings as django_settings

USE_HYPERLINKS = getattr(django_settings, "USE_HYPERLINKS", False)


def context_settings(request):
    """Return all context settings for hyperlinks app."""
    new_settings = {}
    new_settings["USE_HYPERLINKS"] = USE_HYPERLINKS
    return new_settings
