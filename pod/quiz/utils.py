"""Esup-Pod quiz utilities."""

from typing import Optional
from pod.quiz.models import (
    LongAnswerQuestion,
    MultipleChoiceQuestion,
    Quiz,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)
from itertools import chain

from pod.video.models import Video


def get_quiz_questions(
    quiz: Quiz,
) -> list:
    """
    Retrieve all questions associated with a given quiz.

    Args:
        quiz (Quiz): The quiz for which to retrieve the questions.

    Returns:
        list: A list of questions associated with the quiz.
    """
    single_choice_questions = SingleChoiceQuestion.objects.filter(quiz=quiz)
    multiple_choice_questions = MultipleChoiceQuestion.objects.filter(quiz=quiz)
    short_answer_questions = ShortAnswerQuestion.objects.filter(quiz=quiz)
    long_answer_questions = LongAnswerQuestion.objects.filter(quiz=quiz)

    return list(
        chain(
            single_choice_questions,
            multiple_choice_questions,
            short_answer_questions,
            long_answer_questions,
        )
    )


def get_video_quiz(video: Video) -> Optional[Quiz]:
    """
    Retrieve the quiz associated with a given video.

    Args:
        video (Video): The video for which to retrieve the associated quiz.

    Returns:
        Optional[Quiz]: The quiz associated with the video, or None if no quiz is found.
    """
    return Quiz.objects.filter(video=video).first()
