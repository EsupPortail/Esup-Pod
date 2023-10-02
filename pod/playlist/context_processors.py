from django.conf import settings as django_settings

USE_PLAYLIST = getattr(django_settings, "USE_PLAYLIST", True)
USE_FAVORITES = getattr(django_settings, "USE_FAVORITES", True)
DEFAULT_PLAYLIST_THUMBNAIL = getattr(
    django_settings,
    "DEFAULT_PLAYLIST_THUMBNAIL",
    "/static/playlist/img/default-playlist.svg",
)
COUNTDOWN_PLAYLIST_PLAYER = getattr(django_settings, "COUNTDOWN_PLAYLIST_PLAYER", 0)


def context_settings(request):
    """Return all context settings for playlist app"""
    new_settings = {}
    new_settings["USE_PLAYLIST"] = USE_PLAYLIST
    new_settings["USE_FAVORITES"] = USE_FAVORITES
    new_settings["DEFAULT_PLAYLIST_THUMBNAIL"] = DEFAULT_PLAYLIST_THUMBNAIL
    new_settings["COUNTDOWN_PLAYLIST_PLAYER"] = COUNTDOWN_PLAYLIST_PLAYER
    return new_settings
