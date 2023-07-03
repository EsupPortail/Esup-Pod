from django.conf import settings as django_settings

USE_PLAYLIST = getattr(django_settings, "USE_PLAYLIST", True)
USE_FAVORITES = getattr(django_settings, "USE_FAVORITES", True)
DEFAULT_PLAYLIST_THUMBNAIL = getattr(
    django_settings,
    "DEFAULT_PLAYLIST_THUMBNAIL",
    "/static/img/default-playlist.svg"
)


def context_settings(request):
    """Return all context settings for playlist app"""
    new_settings = {}
    new_settings["USE_PLAYLIST"] = USE_PLAYLIST
    new_settings["USE_FAVORITES"] = USE_FAVORITES
    new_settings["DEFAULT_PLAYLIST_THUMBNAIL"] = DEFAULT_PLAYLIST_THUMBNAIL
    return new_settings
