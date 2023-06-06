from django.contrib.auth.models import User
from pod.playlist.models import Playlist

from pod.video.models import Video


def is_ajax(request) -> bool:
    """Check that the request is made by a javascript call."""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def get_number_video_for_user(user: User) -> int():
    """
    Get the number of videos for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of videos.
    """
    return Video.objects.filter(owner=user).count()


def get_number_playlist_for_user(user: User) -> int():
    """
    Get the number of playlists for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of playlist.
    """
    return Playlist.objects.filter(owner=user).count()
