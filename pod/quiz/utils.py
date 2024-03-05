"""Esup-Pod quiz utilities."""

from typing import List, Optional, Union
from pod.quiz.models import (
    LongAnswerQuestion,
    MultipleChoiceQuestion,
    Quiz,
    ShortAnswerQuestion,
    UniqueChoiceQuestion,
)
from itertools import chain

from pod.video.models import Video


def get_quiz_questions(
    quiz: Quiz,
) -> List[
    Union[
        UniqueChoiceQuestion,
        MultipleChoiceQuestion,
        ShortAnswerQuestion,
        LongAnswerQuestion,
    ]
]:
    """
    Retrieve all questions associated with a given quiz.

    Args:
        quiz (Quiz): The quiz for which to retrieve the questions.

    Returns:
        List[Union[UniqueChoiceQuestion, MultipleChoiceQuestion, ShortAnswerQuestion, LongAnswerQuestion]]: A list of questions associated with the quiz.
    """
    unique_choice_questions = UniqueChoiceQuestion.objects.filter(quiz=quiz)
    multiple_choice_questions = MultipleChoiceQuestion.objects.filter(quiz=quiz)
    short_answer_questions = ShortAnswerQuestion.objects.filter(quiz=quiz)
    long_answer_questions = LongAnswerQuestion.objects.filter(quiz=quiz)

    return list(
        chain(
            unique_choice_questions,
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
