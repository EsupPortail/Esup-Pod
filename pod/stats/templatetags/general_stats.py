from django.template import Library

from pod.stats.utils import number_videos, total_time_videos

register = Library()


@register.simple_tag(takes_context=True, name="get_total_time_videos")
def get_total_time_videos(context: dict, video_list=None) -> str:
    """
    Get the total duration time of videos.

    Args:
        video_list : The video object list

    Returns:
        str: The total duration time of videos.
    """
    request = context["request"]

    return total_time_videos(request, video_list)


@register.simple_tag(takes_context=True, name="get_number_videos")
def get_number_videos(context: dict, video_list=None) -> str:
    """
    Get the number of videos.

    Args:
        video_list : The video object list

    Returns:
        str: The number of videos.
    """
    request = context["request"]

    return number_videos(request, video_list)
