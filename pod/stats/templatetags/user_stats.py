from django.template import Library, RequestContext
from pod.playlist.utils import get_number_playlist

from pod.stats.utils import (
    number_channels,
    number_favorites,
    number_files,
    number_meetings,
    number_videos,
)

from pod.video.models import Video

register = Library()


@register.simple_tag(takes_context=True, name="get_number_video_user")
def get_number_video_user(context: RequestContext) -> int:
    """
    Get the number of videos for a user.

    Args:
        context (RequestContext): The context.

    Returns:
        int: The number of videos for the user.
    """
    request = context["request"]
    user_video_list = Video.objects.filter(owner=request.user)
    return number_videos(request, user_video_list)


@register.simple_tag(takes_context=True, name="get_number_playlist_user")
def get_number_playlist_user(context: RequestContext):
    """
    Get the number of playlists for a user.

    Args:
        context (RequestContext): The context.

    Returns:
        int: The number of playlists for the user.
    """
    request = context["request"]
    return get_number_playlist(request.user)


@register.simple_tag(takes_context=True, name="get_number_files_user")
def get_number_files_user(context: RequestContext):
    """
    Get the number of files for a user.

    Args:
        context (RequestContext): The context.

    Returns:
        int: The number of files for the user.
    """
    request = context["request"]
    return number_files(request.user)


@register.simple_tag(takes_context=True, name="get_number_favorites_user")
def get_number_favorites_user(context: RequestContext):
    """
    Get the number of favorites for a user.

    Args:
        context (RequestContext): The context.

    Returns:
        int: The number of favorites for user.
    """
    request = context["request"]
    return number_favorites(request.user)


@register.simple_tag(takes_context=True, name="get_number_meetings_user")
def get_number_meetings_user(context: RequestContext):
    """
    Get the number of meetings for a user.

    Args:
        context (RequestContext): The context.

    Returns:
        int: The number of meetings for user.
    """
    request = context["request"]
    return number_meetings(request.user)


@register.simple_tag(takes_context=True, name="get_number_channels")
def get_number_channels(context: RequestContext, target: str = None):
    """
    Get the number of channels for a user.

    Args:
        context (RequestContext): The context.
        target (str, optional): The target can be "user" or "None". Defaults to None.

    Returns:
        int: The number of channels for user if the target is "user", or the number of all channels if target is "None".
    """
    request = context["request"]
    return number_channels(request, target)
