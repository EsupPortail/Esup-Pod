"""Esup-Pod playlist utilities."""

from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.sites.models import Site
from django.db.models.functions import Lower
from django.db.models import Max, QuerySet
from django.urls import reverse
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render
from django.http import Http404
from django.utils.translation import gettext as _

from pod.video.models import Video
from pod.video.utils import get_video_access
from django.conf import settings

from .apps import FAVORITE_PLAYLIST_NAME
from .models import Playlist, PlaylistContent

import hashlib


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
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object.
        video (:class:`pod.video.models.Video`): The video object.

    Returns:
        str: The status message.
    """
    if not check_video_in_playlist(playlist, video):
        PlaylistContent.objects.create(
            playlist=playlist, video=video, rank=get_next_rank(playlist)
        )


def user_remove_video_from_playlist(playlist: Playlist, video: Video) -> str:
    """
    Remove a video from playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object.
        video (:class:`pod.video.models.Video`): The video object.

    Returns:
        str: The status message.
    """
    if check_video_in_playlist(playlist, video):
        PlaylistContent.objects.filter(playlist=playlist, video=video).delete()


def get_next_rank(playlist: Playlist) -> int:
    """
    Get the next rank in playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object.

    Returns:
        int: The next rank.
    """
    last_rank = PlaylistContent.objects.filter(playlist=playlist).aggregate(Max("rank"))[
        "rank__max"
    ]
    return last_rank + 1 if last_rank is not None else 1


def get_number_playlist(user: User) -> int:
    """
    Get the number of playlist for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object.

    Returns:
        int: The number of playlist.
    """
    return Playlist.objects.filter(owner=user, site=Site.objects.get_current()).count()


def get_number_video_in_playlist(playlist: Playlist) -> int:
    """
    Get the number of video in a playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object.

    Returns:
        int: The number of video in the playlist.
    """
    return PlaylistContent.objects.filter(playlist=playlist).count()


def get_number_video_added_in_playlist(video: Video) -> int:
    """
    Get the number of times a video has been added to a playlist.

    Args:
        video (:class:`pod.video.models.Video`): The video object

    Returns:
        int: The number of times a video has been added to a playlist
    """
    return PlaylistContent.objects.filter(video=video).count()


def get_number_video_added_in_specific_playlist(playlist: Playlist) -> int:
    """
    Get the number of times a video has been added to a specific playlist.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object

    Returns:
        int: The number of times a video has been added to the specific playlist
    """
    return PlaylistContent.objects.filter(playlist=playlist).count()


def get_public_playlist() -> list:
    """
    Get all public playlists in the application.

    Returns:
        list(:class:`pod.playlist.models.Playlist`): The public playlist list
    """
    return Playlist.objects.filter(visibility="public", site=Site.objects.get_current())


def get_promoted_playlist() -> list:
    """
    Get all promoted playlists in the application.

    Returns:
        list(:class:`pod.playlist.models.Playlist`): The public playlist list
    """
    return Playlist.objects.filter(promoted=True, site=Site.objects.get_current())


def get_playlist_list_for_user(user: User) -> list:
    """
    Get all playlist for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        list(:class:`pod.playlist.models.Playlist`): The playlist list for a user
    """
    if getattr(settings, "USE_FAVORITES", True):
        return Playlist.objects.filter(owner=user, site=Site.objects.get_current())
    else:
        return Playlist.objects.filter(
            owner=user, site=Site.objects.get_current()
        ).exclude(name="Favorites")


def get_video_list_for_playlist(
    playlist: Playlist, *, prefetch_access: bool = False
) -> QuerySet[Video]:
    """
    Get a playlist's videos, optionally loading relations used for access checks.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object
        prefetch_access (bool): Preload group restrictions and additional owners.

    Returns:
        QuerySet[Video]: The playlist videos with their ranks.
    """
    playlist_content = PlaylistContent.objects.filter(playlist=playlist)
    videos_id = playlist_content.values_list("video_id", flat=True)
    video_list = Video.objects.filter(id__in=videos_id).extra(
        select={"rank": "playlist_playlistcontent.rank"},
        tables=["playlist_playlistcontent"],
        where=[
            "playlist_playlistcontent.video_id=video_video.id",
            "playlist_playlistcontent.playlist_id=%s",
        ],
        params=[playlist.id],
    )
    if prefetch_access:
        video_list = video_list.prefetch_related(
            "restrict_access_to_groups", "additional_owners"
        )
    return video_list


def get_playlist(slug: str) -> Playlist:
    """
    Get a playlist with a slug.

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
    return Playlist.objects.get(
        name=FAVORITE_PLAYLIST_NAME, owner=user, site=Site.objects.get_current()
    )


def remove_playlist(user: User, playlist: Playlist) -> None:
    """
    Remove playlist if the user has right to do it.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object
        playlist (:class:`pod.playlist.models.Playlist`): The playlist objet
    """
    if not user_can_delete_playlist(user, playlist):
        raise PermissionDenied
    playlist.delete()


def user_can_manage_playlist(user: User, playlist: Playlist) -> bool:
    """Allow owners, co-owners and administrators to manage playlist contents."""
    return user.is_authenticated and (
        playlist.owner_id == user.pk
        or user.is_superuser
        or playlist.additional_owners.filter(pk=user.pk).exists()
    )


def user_can_delete_playlist(user: User, playlist: Playlist) -> bool:
    """Reserve deletion to the owner and administrators, excluding system playlists."""
    return (
        playlist.editable
        and user.is_authenticated
        and (playlist.owner_id == user.pk or user.is_superuser)
    )


@transaction.atomic
def reorganize_playlist(playlist: Playlist, swaps: dict) -> None:
    """Apply validated swaps atomically without invoking automatic rank assignment."""
    contents = {
        content.video.slug: content
        for content in PlaylistContent.objects.select_for_update()
        .filter(playlist=playlist)
        .select_related("video")
    }
    for pair in swaps.values():
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("A swap must contain two video slugs")
        first, second = (contents[slug] for slug in pair)
        first.rank, second.rank = second.rank, first.rank
    PlaylistContent.objects.bulk_update(contents.values(), ["rank"])


def get_playlists_for_additional_owner(user: User) -> list:
    """
    Get playlist list for a specific additional owner.

    Args:
        user (:class:`django.contrib.auth.models.User`): The specific onwer

    Returns:
        list (:class:`list(pod.playlist.models.Playlist)`): The list of playlist
    """
    return Playlist.objects.filter(
        additional_owners=user, site=Site.objects.get_current()
    )


def get_additional_owners(playlist: Playlist) -> list:
    """
    Get additional owners list.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The playlist objet

    Returns:
        list (:class:`list(pod.authentication.models.Owner)`): The list of additional owners
    """
    return playlist.additional_owners.all()


def get_link_to_start_playlist(
    request: WSGIRequest, playlist: Playlist, video=None
) -> str:
    """
    Get the link to start a specific playlist.

    Args:
        request (WSGIRequest): The WSGIRequest
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist
        video (:class:`pod.video.models.Video`): The video object, optionnal. Default to None

    Returns:
        str: Link to start the playlist.
    """
    if video:
        return (
            f"{reverse('video:video', kwargs={'slug': video})}?playlist={playlist.slug}"
        )
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
    favorites_playlists = Playlist.objects.filter(name=FAVORITE_PLAYLIST_NAME)
    favorite_contents = PlaylistContent.objects.filter(
        playlist__in=favorites_playlists, video=video
    )
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


def user_can_see_playlist_video(
    request: WSGIRequest, video: Video, playlist: Playlist
) -> bool:
    """
    Check video permissions within a playlist, independently of its password gate.

    Args:
        request (WSGIRequest): The WSGIRequest
        video (:class:`pod.video.models.Video`): The video object
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object

    Returns:
        bool: True if the user can see the playlist video. False otherwise
    """
    if playlist.visibility not in {
        "public",
        "protected",
    } and not user_can_manage_playlist(request.user, playlist):
        return False
    if video.password:
        return request.user.is_authenticated and (
            video.owner_id == request.user.pk
            or request.user.is_superuser
            or request.user.has_perm("video.change_video")
            or request.user in video.additional_owners.all()
        )
    return get_video_access(request, video, None)


def sort_playlist_list(playlist_list: list, sort_field: str, sort_direction="") -> list:
    """
    Return playlist list sorted by specific column name and asc or desc direction.

    Args:
        playlist_list (:class:`list(pod.playlist.models.Playlist)`): The list of playlist
        sort_field (str): The specific column name to sort
        sort_direction (str): The direction of sort (ascending or descending)

    Returns:
        list (:class:`list(pod.playlist.models.Playlist)`): The list of playlist
    """
    if sort_field and sort_field in {
        "id",
        "name",
        "visibility",
        "slug",
        "owner",
        "date_created",
        "date_updated",
    }:
        if sort_field in {"name"}:
            sort_field = Lower(sort_field)
            if not sort_direction:
                sort_field = sort_field.desc()

        elif not sort_direction:
            sort_field = "-" + sort_field
        playlist_list = playlist_list.order_by(sort_field)

    return playlist_list.distinct()


def check_password(form_password: str, playlist: Playlist) -> bool:
    """
    Check if the form password is correct for the playlist.

    Args:
        form_password (str): Password provided by user
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist


    Returns:
        bool: `True` if the password provided matches the playlist password, `False` otherwise.
    """
    hashed_password = hashlib.sha256(form_password.encode("utf-8")).hexdigest()
    return hashed_password == playlist.password


def playlist_can_be_displayed(request: WSGIRequest, playlist: Playlist) -> bool:
    """
    Check if the playlist can be displayed by the current user.

    Args:
        request (:class:`django.core.handlers.wsgi.WSGIRequest`): The current request.
        playlist (:class:`pod.playlist.models.Playlist`): The playlist object.

    Returns:
        bool: `True` if the current user can be see the playlist, `False` otherwise.
    """
    return (
        playlist.visibility == "public"
        or user_can_manage_playlist(request.user, playlist)
        or (
            playlist.visibility == "protected"
            and request.session.get(f"playlist_access_{playlist.pk}")
            == playlist.get_session_auth_hash()
        )
    )


def require_playlist_access(request: WSGIRequest, playlist: Playlist):
    """Return a password form when access is missing, or reject a private playlist."""
    from .forms import PlaylistPasswordForm

    if playlist_can_be_displayed(request, playlist):
        return None
    if playlist.visibility != "protected":
        messages.error(request, _("You cannot access this playlist."))
        raise PermissionDenied(_("You cannot access this playlist."))
    form = PlaylistPasswordForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        password = form.cleaned_data["password"]
        # New passwords are normalized; legacy hashes may include surrounding spaces.
        if check_password(password.strip(), playlist) or check_password(
            password, playlist
        ):
            request.session[f"playlist_access_{playlist.pk}"] = (
                playlist.get_session_auth_hash()
            )
            return None
        form.add_error("password", _("The password is incorrect."))
    return render(
        request,
        "playlist/protected-playlist-form.html",
        {"form": form, "playlist": playlist},
    )


def require_playlist_video_access(request: WSGIRequest, video: Video, playlist: Playlist):
    """Check playlist membership and video permissions for every player variant."""
    response = require_playlist_access(request, playlist)
    if response is not None:
        return response
    if not PlaylistContent.objects.filter(playlist=playlist, video=video).exists():
        raise Http404
    if not user_can_see_playlist_video(request, video, playlist):
        raise PermissionDenied
    return None
