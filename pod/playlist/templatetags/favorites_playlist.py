from django.template import Library

from pod.playlist.utils import check_video_in_playlist, get_favorite_playlist_for_user
from pod.video.models import Video

from ..models import Playlist

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
        bool: True if the user has the video as favorite, False otherwise
    """
    return check_video_in_playlist(get_favorite_playlist_for_user(user), video)
