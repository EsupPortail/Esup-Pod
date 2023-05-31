from django.conf import settings as django_settings

USE_PLAYLIST = getattr(django_settings, "USE_PLAYLIST", True)


def context_settings(request):
    """Return all context settings for playlist app"""
    new_settings = {}
    new_settings["USE_PLAYLIST"] = USE_PLAYLIST
    return new_settings
