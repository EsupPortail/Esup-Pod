"""Esup-Pod quiz utilities."""

from pod.quiz.models import (
    LongAnswerQuestion,
    MultipleChoiceQuestion,
    Quiz,
    ShortAnswerQuestion,
    UniqueChoiceQuestion,
)
from itertools import chain

from pod.video.models import Video


def get_quiz_questions(quiz: Quiz):
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


def get_video_quiz(video: Video):
    return Quiz.objects.get(video=video)
