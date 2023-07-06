from django.template import Library

from pod.video.models import Video
from ..models import Playlist
from ..utils import (
    get_count_video_added_in_playlist as total_additions_playlist_utils,
    get_total_favorites_video as total_favorites_utils,
    get_number_video_added_in_specific_playlist,
)

register = Library()


@register.simple_tag(takes_context=True, name="get_number_favorites")
def get_number_favorites(context: dict) -> int:
    """
    Get the number of times a video has been added to a specific playlist

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object

    Returns:
        int: The number of times a video has been added to the specific playlist
    """
    user = context["request"].user
    favorites_playlist = Playlist.objects.get(name="Favorites", owner=user)
    return get_number_video_added_in_specific_playlist(favorites_playlist)


@register.simple_tag(name="get_total_favorites_video")
def get_total_favorites_video(video: Video) -> int:
    """
    Get the number of videos added in favorites playlist.

    Args:
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        int: The number of videos added in favorites playlist.
    """
    return total_favorites_utils(video)


@register.simple_tag(name="get_count_video_added_in_playlist")
def get_count_video_added_in_playlist(video: Video) -> int:
    """
    Get the number of video added in any playlist (including favorites).

    Args:
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        int: The number of videos added in playlists.
    """
    return total_additions_playlist_utils(video)
