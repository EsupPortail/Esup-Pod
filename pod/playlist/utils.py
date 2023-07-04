"""Esup-Pod playlist utilities."""
from django.contrib.auth.models import User
from django.db.models import Max
from django.urls import reverse

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


def get_favorite_playlist_for_user(user: User) -> Playlist:
    """
    Get the favorite playlist of a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        Playlist: The favorite playlist
    """
    return Playlist.objects.get(name="Favorites", owner=user)


def remove_playlist(user: User, playlist: Playlist) -> None:
    """
    Remove playlist if the user has right to do it.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object
        playlist (:class:`pod.playlist.models.Playlist`): The playlist objet
    """
    if playlist.owner == user or user.is_staff:
        playlist.delete()


def get_playlists_for_additional_owner(user: User) -> list:
    """
    Get playlist list for a specific additional owner.

    Args:
        user (:class:`django.contrib.auth.models.User`): The specific onwer.

    Returns:
        list (:class:`list(pod.playlist.models.Playlist)`): The list of playlist.
    """
    return Playlist.objects.filter(additional_owners=user)


def get_additional_owners(playlist: Playlist) -> list:
    """
    Get additional owners list.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist objet

    Returns:
        list (:class:`list(pod.authentication.models.Owner)`): The list of additional owners.
    """
    return playlist.additional_owners.all()


def get_link_to_start_playlist(request, playlist: Playlist) -> str:
    """
    Get the link to start a specific playlist.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user.
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist.

    Returns:
        str: Link to start the playlist.
    """
    first_video = playlist.get_first_video(request)
    if first_video:
        return f"{reverse('video:video', kwargs={'slug': first_video.slug})}?playlist={playlist.slug}"
    else:
        return ""


def get_total_favorites_video(video: Video) -> int:
    """
    Get the number of videos added in favorites playlist.

    Args:
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        int: The number of videos added in favorites playlist.
    """
    favorites_playlists = Playlist.objects.filter(name="Favorites")
    favorite_contents = PlaylistContent.objects.filter(
        playlist__in=favorites_playlists, video=video)
    count = favorite_contents.count()
    return count


def get_count_video_added_in_playlist(video: Video) -> int:
    """
    Get the number of video added in any playlist (including favorites).

    Args:
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        int: The number of videos added in playlists.
    """
    return PlaylistContent.objects.filter(video=video).count()


def user_can_see_playlist_video(request: dict, video: Video) -> bool:
    is_password_protected = video.password is not None and video.password != ""
    if is_password_protected or video.is_draft:
        if not request.user.is_authenticated:
            return False
        return (
            (video.owner == request.user)
            or (request.user in video.additional_owners.all())
            or (request.user.is_staff)
        )
    else:
        return True


def sort_playlist_list(playlist_list, sort_field, sort_direction=""):
    """Return playlists list sorted by sort_field.

    Sorted by specific column name and ascending or descending direction
    """
    if sort_field and sort_field in [
        "name",
        "modification_date",
    ]:
        if not sort_direction:
            sort_field = "-" + sort_field
        playlist_list = playlist_list.order_by(sort_field)
    return playlist_list.distinct()