from django.template import Library

from pod.video.models import Video

from ..utils import (
    get_count_video_added_in_playlist as total_additions_playlist_utils,
    get_total_favorites_video as total_favorites_utils,
)

register = Library()


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
