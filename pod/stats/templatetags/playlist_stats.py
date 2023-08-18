from django.template import Library
from pod.playlist.models import Playlist

from pod.video.models import Video

from pod.playlist.utils import (
    get_additional_owners,
    get_count_video_added_in_playlist as total_additions_playlist_utils,
    get_total_favorites_video as total_favorites_utils,
    get_number_video_in_playlist as total_videos_in_playlist,
    playlist_visibility,
)

register = Library()


@register.simple_tag(name="get_total_favorites_video")
def get_total_favorites_video(video: Video) -> int:
    """
    Get the total number of times a video has been marked as a favorite.

    Args:
        video (:class:`pod.video.models.Video`): The video for which to retrieve the total number of favorites.

    Returns:
        int: The total number of favorites for the video.
    """
    return total_favorites_utils(video)


@register.simple_tag(name="get_count_video_added_in_playlist")
def get_count_video_added_in_playlist(video: Video) -> int:
    """
    Get the total number of times a video has been added to playlists.

    Args:
        video (:class:`pod.video.models.Video`): The video for which to retrieve the total number of additions to playlists.

    Returns:
        int: The total number of additions to playlists for the video.
    """
    return total_additions_playlist_utils(video)


@register.simple_tag(name="get_number_video_in_playlist")
def get_number_video_in_playlist(playlist: Playlist) -> int:
    """
    Get the number of videos in a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist for which to retrieve the number of videos.

    Returns:
        int: The number of videos in the playlist.
    """
    return total_videos_in_playlist(playlist)


@register.simple_tag(name="get_number_additional_owners_playlist")
def get_number_additional_owners_playlist(playlist: Playlist) -> int:
    """
    Get the number of additional owners of a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist for which to retrieve the number of additional owners.

    Returns:
        int: The number of additional owners of the playlist.
    """
    return get_additional_owners(playlist).count()


@register.simple_tag(name="get_playlist_visibility")
def get_playlist_visibility(playlist: Playlist) -> str:
    """
    Get the visibility status of a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist for which to retrieve the visibility status.

    Returns:
        str: The visibility status of the playlist.
    """
    return playlist_visibility(playlist)
