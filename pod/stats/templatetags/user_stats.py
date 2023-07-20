from django.template import Library

from pod.stats.utils import number_playlist, number_videos

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
    print(request)
    print(request.user)
    return number_playlist(request.user)
