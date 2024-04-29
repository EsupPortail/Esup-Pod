"""Esup-Pod context processors for cut app."""

from django.conf import settings as django_settings

USE_CUT = getattr(django_settings, "USE_CUT", True)


def context_settings(request):
    """Return all context settings for cut app."""
    new_settings = {}
    new_settings["USE_CUT"] = USE_CUT
    return new_settings
