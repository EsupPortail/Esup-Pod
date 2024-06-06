"""Esup-Pod ai_enhancement context_processors."""

from django.conf import settings as django_settings

USE_AI_ENHANCEMENT = getattr(
    django_settings,
    "USE_AI_ENHANCEMENT",
    False,
)


def context_settings(request):
    """Return all context settings for ai_enhancement app"""
    new_settings = {
        "USE_AI_ENHANCEMENT": USE_AI_ENHANCEMENT,
    }
    return new_settings
