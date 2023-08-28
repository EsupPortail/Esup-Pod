from django.template import Library
from django.contrib.auth.models import User

from pod.video.models import Video
from ..models import Playlist
from ..utils import (
    check_video_in_playlist,
    get_playlist_list_for_user,
    get_playlists_for_additional_owner
)

register = Library()


@register.simple_tag(name="get_user_playlists")
def get_user_playlists(user: User) -> list:
    """
    Get all playlist for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        list (:class:`list(pod.playlist.models.Playlist)`): The list of playlist.
    """
    return get_playlist_list_for_user(user) | get_playlists_for_additional_owner(user)


@register.simple_tag(name="video_in_playlist")
def video_in_playlist(playlist: Playlist, video: Video) -> bool:
    """
    Verify if a video is present in a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        bool: True if the video is on the playlist, False otherwise
    """
    return check_video_in_playlist(playlist, video)
