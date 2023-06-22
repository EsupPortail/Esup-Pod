from django.template import Library
from pod.playlist.models import Playlist
from django.utils.translation import ugettext_lazy as _

from pod.playlist.utils import (
    check_video_in_playlist,
    get_favorite_playlist_for_user,
    get_playlist_list_for_user,
    get_playlists_for_additional_owner,
)
from pod.video.models import Video


register = Library()


@register.simple_tag(name="get_favorite_playlist")
def get_favorite_playlist(user):
    return get_favorite_playlist_for_user(user)


@register.simple_tag(name="is_favorite")
def is_favorite(user, video: Video) -> bool:
    """
    Template tag to check if the user has this video as favorite.

    Args:
        context (dict): The template context dictionary
        video (:class:`pod.video.models.Video`): The video entity to check

    Returns:
        bool: `True` if the user has the video as favorite, `False` otherwise
    """
    return check_video_in_playlist(get_favorite_playlist_for_user(user), video)


@register.simple_tag(name="get_playlist_name")
def get_playlist_name(playlist: Playlist) -> str:
    """
    Get the playlist name.

    Args:
        playlist (:class:`pod.playlist.models.Playlist`): The specific playlist

    Returns:
        str: The favorites playlist name
    """
    if playlist.name == "Favorites":
        return _("Favorites")
    else:
        return playlist.name


@register.simple_tag(takes_context=True, name="can_see_favorite_video")
def can_see_favorite_video(context: dict, video: Video) -> bool:
    """
    Template tag to check if the user can see a playlist video.

    Args:
        context (dict): The template context dictionary
        video (:class:`pod.video.models.Video`): The video entity to check

    Returns:
        bool: `True` if the user can, `False` otherwise
    """
    request = context["request"]
    is_password_protected = video.password is not None and video.password != ""
    if is_password_protected or video.is_draft:
        if not request.user.is_authenticated:
            return False
        return (video.owner == request.user) or (request.user in video.additional_owners.all())
    else:
        return True
