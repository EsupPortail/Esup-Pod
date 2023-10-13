"""Template tags used for playlist application buttons."""

from django.template import Library

from pod.video.models import Video
from ..models import Playlist
from ..utils import (
    get_additional_owners,
    get_link_to_start_playlist as get_link_to_start_playlist_util,
    user_can_see_playlist_video,
)

register = Library()


@register.simple_tag(takes_context=True, name="user_can_edit_or_remove")
def user_can_edit_or_remove(context: dict, playlist: Playlist) -> bool:
    """
    Template tag used to check if the user can edit or remove a specific playlist.

    Args:
        context (dict): The context.
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist.

    Returns:
        bool: `True` if the user can do it. `False` otherwise.
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return playlist.editable and (request.user == playlist.owner or request.user.is_staff or request.user in get_additional_owners(playlist))


@register.simple_tag(takes_context=True, name="get_link_to_start_playlist")
def get_link_to_start_playlist(context: dict, playlist: Playlist, video=None) -> str:
    """
    Template tag used to get the link to start a specific playlist.

    Args:
        context (dict): The context.
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist.
        video (:class:`pod.video.models.Video`): The video entity to check, default to None


    Returns:
        str: Link to start the playlist.
    """
    request = context["request"]
    return get_link_to_start_playlist_util(request, playlist, video)


@register.simple_tag(takes_context=True, name="can_see_playlist_video")
def can_see_playlist_video(context: dict, video: Video) -> bool:
    """
    Template tag to check if the user can see a playlist video.

    Args:
        context (dict): The template context dictionary
        video (:class:`pod.video.models.Video`): The video entity to check

    Returns:
        bool: `True` if the user can, `False` otherwise
    """
    return user_can_see_playlist_video(context["request"], video)
