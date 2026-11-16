"""Esup-Pod quiz context processor."""

from django.conf import settings as django_settings

USE_QUIZ = getattr(django_settings, "USE_QUIZ", False)


def context_settings(request):
    """Return all context settings for quiz app."""
    new_settings = {}
    new_settings["USE_QUIZ"] = USE_QUIZ
    return new_settings
