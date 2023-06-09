"""Template tags used for playlist application buttons."""

from django.template import Library

from ..models import Playlist
from ..utils import get_link_to_start_playlist as get_link_to_start_playlist_util

register = Library()


@register.simple_tag(takes_context=True, name="user_can_edit_or_remove")
def user_can_edit_or_remove(context: dict, playlist: Playlist) -> bool:
    """
    Template tag used to check if the user can edit or remove a specific playlist.

    Args:
        context (dict): The context.
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist;

    Returns:
        bool: `True` if the user can do it. `False` otherwise.
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False
    return playlist.editable and (request.user == playlist.owner or request.user.is_staff)


@register.simple_tag(takes_context=True, name="get_link_to_start_playlist")
def get_link_to_start_playlist(context: dict, playlist: Playlist) -> str:
    """
    Template tag used to get the link to start a specific playlist.

    Args:
        context (dict): The context.
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist.

    Returns:
        str: Link to start the playlist.
    """
    request = context["request"]
    return get_link_to_start_playlist_util(request.user, playlist)
