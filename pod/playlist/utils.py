"""Esup-Pod playlist utilities."""
from django.contrib.auth.models import User
from django.db.models import Max


from pod.playlist.models import Playlist, PlaylistContent
from pod.video.models import Video


def check_video_in_playlist(playlist: Playlist, video: Video) -> bool:
    """
    Verify if a video is present in a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        bool: True if the video is on the playlist, False otherwise
    """
    return PlaylistContent.objects.filter(playlist=playlist, video=video).exists()


def user_has_playlist(user: User) -> bool:
    """
    Check if a user has a playlist.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        bool: True if the user has a playlist, False otherwise
    """
    return get_number_playlist(user) > 0


def user_add_video_in_playlist(playlist: Playlist, video: Video) -> str:
    """
    Add a video in playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        str: The status message
    """
    if not check_video_in_playlist(playlist, video):
        PlaylistContent.objects.create(
            playlist=playlist,
            video=video,
            rank=get_next_rank(playlist)
        )


def user_remove_video_from_playlist(playlist: Playlist, video: Video) -> str:
    """
    Remove a video from playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        str: The status message
    """
    if check_video_in_playlist(playlist, video):
        PlaylistContent.objects.filter(playlist=playlist, video=video).delete()


def get_next_rank(playlist: Playlist) -> int:
    """
    Get the next rank in playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object

    Returns:
        int: The next rank
    """
    last_rank = PlaylistContent.objects.filter(
        playlist=playlist).aggregate(Max("rank"))["rank__max"]
    return last_rank + 1 if last_rank is not None else 1


def get_number_playlist(user: User) -> int:
    """
    Get the number of playlist for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of playlist
    """
    return Playlist.objects.filter(owner=user).count()


def get_number_video_in_playlist(playlist: Playlist) -> int:
    """
    Get the number of video in a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object

    Returns:
        int: The number of video in the playlist
    """
    return PlaylistContent.objects.filter(playlist=playlist).count()


def get_number_video_added_in_playlist(video: Video) -> int:
    """
    Get the number of times a video has been added to a playlist

    Args:
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        int: The number of times a video has been added to a playlist
    """
    return PlaylistContent.objects.filter(video=video).count()


def get_number_video_added_in_specific_playlist(playlist: Playlist) -> int:
    """
    Get the number of times a video has been added to a specific playlist

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object

    Returns:
        int: The number of times a video has been added to the specific playlist
    """
    return PlaylistContent.objects.filter(playlist=playlist).count()


def get_public_playlist() -> list:
    """
    Get all public playlist in the application.

    Returns:
        list(:class:`pod.playlist.models.Playlist`): The public playlist list
    """
    return Playlist.objects.filter(visibility="public")


def get_playlist_list_for_user(user: User) -> list:
    """
    Get all playlist for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        list(:class:`pod.playlist.models.Playlist`): The playlist list for a user
    """
    return Playlist.objects.filter(owner=user)


def get_video_list_for_playlist(playlist: Playlist) -> list:
    """
    Get all videos for a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object

    Returns:
        list(:class:`pod.video.models.Video`): The video list for a playlist
    """
    playlist_content = PlaylistContent.objects.filter(playlist=playlist)
    videos_id = playlist_content.values_list("video_id", flat=True)
    video_list = Video.objects.filter(id__in=videos_id).extra(
        select={"rank": "playlist_playlistcontent.rank"},
        tables=["playlist_playlistcontent"],
        where=[
            "playlist_playlistcontent.video_id=video_video.id",
            "playlist_playlistcontent.playlist_id=%s"
        ],
        params=[playlist.id]
    )
    return video_list


def get_playlist(slug: str) -> Playlist:
    """
    Get a playlist with a slug

    Args:
        slug (str): The slug of the playlist

    Returns:
        Playlist(:class:`pod.playlist.models.Playlist`): The playlist object
    """
    return Playlist.objects.get(slug=slug)


def remove_playlist(user: User, playlist: Playlist) -> None:
    """
    Remove playlist if the user has right to do it.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object
        playlist (:class:`pod.playlist.models.Playlist`): The playlist objet
    """
    if playlist.owner == user or user.is_staff:
        playlist.delete()
