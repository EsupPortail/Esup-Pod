from django.template import Library

from pod.stats.utils import (
    number_channels,
    number_favorites,
    number_files,
    number_meetings,
    number_playlist,
    number_videos,
)

from pod.video.models import Video

register = Library()


@register.simple_tag(takes_context=True, name="get_number_video_user")
def get_number_video_user(context):
    """
    Get the number of videos for a user.

    Args:
        context : The context.

    Returns:
        int: The number of videos for user.
    """

    request = context["request"]
    user_video_list = Video.objects.filter(owner=request.user)
    return number_videos(request, user_video_list)


@register.simple_tag(takes_context=True, name="get_number_playlist_user")
def get_number_playlist_user(context):
    request = context["request"]
    return number_playlist(request.user)


@register.simple_tag(takes_context=True, name="get_number_files_user")
def get_number_files_user(context):
    request = context["request"]
    return number_files(request.user)


@register.simple_tag(takes_context=True, name="get_number_favorites_user")
def get_number_favorites_user(context):
    request = context["request"]
    return number_favorites(request.user)


@register.simple_tag(takes_context=True, name="get_number_meetings_user")
def get_number_meetings_user(context):
    request = context["request"]
    return number_meetings(request.user)


@register.simple_tag(takes_context=True, name="get_number_channels_user")
def get_number_channels_user(context):
    request = context["request"]
    return number_channels(request)
