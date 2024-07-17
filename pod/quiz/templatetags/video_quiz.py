"""Template tags used for Esup-Pod video quiz."""

from django.template import Library
from pod.quiz.models import Quiz
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
    quiz = get_video_quiz(video)
    if quiz:
        request = context["request"]
        if quiz.is_draft:
            return video.owner == request.user or request.user.is_superuser
        if (
            quiz.connected_user_only and request.user.is_authenticated
        ) or not quiz.connected_user_only:
            return True
    return False


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


@register.simple_tag(name="get_question_color")
def get_question_color(is_submitted_quiz: bool, quiz: Quiz, score: int = None) -> str:
    """
    Template tag used to return a color corresponding to the score.

    Args:
        is_submitted_quiz (bool): True if form is submitted.
        score (int): A question score (from 0 to 1)


    Returns:
        str: The corresponding bootstrap color.
    """
    if quiz.show_correct_answers and is_submitted_quiz and score is not None:
        if score <= 0.5:
            return "danger"
        elif score <= 0.75:
            return "warning"
        return "success"
    return "gray"
