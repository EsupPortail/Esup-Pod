"""Template tags used for video quiz."""

from django.template import Library
from pod.quiz.utils import get_video_quiz

from pod.video.models import Video


register = Library()


@register.simple_tag(takes_context=True, name="is_quiz_accessible")
def is_quiz_accessible(context: dict, video: Video) -> bool:
    """
    Template tag used to know if a quiz is accessible or not.

    Args:
        video (:class:`pod.video.models.Video`): The specific video.


    Returns:
        bool: True if the video is accessible.
    """
    if get_video_quiz(video):
        quiz = get_video_quiz(video)
        request = context["request"]
        print(quiz.connected_user_only)
        if quiz.connected_user_only and not request.user.is_authenticated:
            return False
    return True


@register.simple_tag(name="is_quiz_exists")
def is_quiz_exists(video: Video) -> bool:
    """
    Template tag used to check if the quiz of the video exists.

    Args:
        Video (:class:`pod.video.models.Video`): The specific video.


    Returns:
        bool: True if the quiz exists.
    """
    if get_video_quiz(video):
        return True
    return False
