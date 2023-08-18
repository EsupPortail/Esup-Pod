from typing import List
from django.template import Library, RequestContext

from pod.stats.utils import number_users, number_videos, total_time_videos
from pod.video.models import Video

register = Library()


@register.simple_tag(takes_context=True, name="get_total_time_videos")
def get_total_time_videos(context: RequestContext, video_list: List[Video] = None) -> str:
    """
    Get the total duration of videos in the specified list.

    Args:
        context (RequestContext): The context.
        video_list (List[Video], optional): The list of videos. Defaults to None.

    Returns:
        str: The formatted total duration of videos in HH:MM:SS format.
    """
    request = context["request"]
    return total_time_videos(request, video_list)


@register.simple_tag(takes_context=True, name="get_number_videos")
def get_number_videos(context: RequestContext, video_list: List[Video] = None) -> int:
    """
    Get the total number of videos in the specified list.

    Args:
        context (RequestContext): The context.
        video_list (List[Video], optional): The list of videos. Defaults to None.

    Returns:
        int: The total number of videos.
    """
    request = context["request"]
    return number_videos(request, video_list)


@register.simple_tag(takes_context=False, name="get_number_users")
def get_number_users() -> int:
    """
    Get the total number of users.

    Returns:
        int: The total number of users.
    """
    return number_users()
