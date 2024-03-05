"""Template tags used for video quiz."""

from django.template import Library
from pod.quiz.utils import get_video_quiz

from pod.video.models import Video


register = Library()


@register.simple_tag(takes_context=True, name="is_quiz_accessible")
def is_quiz_accessible(context: dict, video: Video) -> bool:
    """
    Template tag used to get the quiz of the video.

    Args:
        Video (:class:`pod.video.models.Video`): The specific video.


    Returns:
        str: Link to start the playlist.
    """
    if get_video_quiz(video):
        quiz = get_video_quiz(video)
        request = context["request"]
        if quiz.connected_user_only and request.user.is_authenticated:
            return True
    return False


@register.simple_tag(name="is_quiz_exists")
def is_quiz_exists(video: Video) -> bool:
    """
    Template tag used to check if the quiz of the video.

    Args:
        Video (:class:`pod.video.models.Video`): The specific video.


    Returns:
        str: Link to start the playlist.
    """
    if get_video_quiz(video):
        return True
    return False
