from django.template import Library
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from pod.video.models import Video

from ..apps import FAVORITE_PLAYLIST_NAME
from ..models import Playlist
from ..utils import (
    check_video_in_playlist,
    get_favorite_playlist_for_user,
)


register = Library()


@register.simple_tag(name="get_favorite_playlist")
def get_favorite_playlist(user: User) -> Playlist:
    """
    Get the favorite playlist of a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        Playlist: The favorite playlist
    """
    return get_favorite_playlist_for_user(user)


@register.simple_tag(name="is_favorite")
def is_favorite(user: User, video: Video) -> bool:
    """
    Template tag to check if the user has this video as favorite.

    Args:
        context (dict): The template context dictionary
        user (:class:`django.contrib.auth.models.User`): The user object
        video (:class:`pod.video.models.Video`): The video entity to check

    Returns:
        bool: `True` if the user has the video as favorite, `False` otherwise
    """
    return check_video_in_playlist(get_favorite_playlist_for_user(user), video)


@register.simple_tag(name="get_playlist_name")
def get_playlist_name(playlist: Playlist) -> str:
    """
    Get the playlist name.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist.

    Returns:
        str: The playlist name.
    """
    if playlist.name == FAVORITE_PLAYLIST_NAME:
        return _("Favorites")
    else:
        return playlist.name


@register.simple_tag(name="get_playlist_description")
def get_playlist_description(playlist: Playlist) -> str:
    """
    Get the playlist description.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist.

    Returns:
        str: The playlist name.
    """
    if playlist.name == FAVORITE_PLAYLIST_NAME:
        return _("Your favorites videos.")
    else:
        return playlist.description
