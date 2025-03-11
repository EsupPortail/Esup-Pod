"""Esup-Pod quiz utilities."""

import ast
from pod.quiz.models import (
    MultipleChoiceQuestion,
    Question,
    Quiz,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)
from itertools import chain

from pod.video.models import Video
from pod.video_encode_transcript.utils import time_to_seconds

import json


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

    return list(
        chain(
            single_choice_questions,
            multiple_choice_questions,
            short_answer_questions,
        )
    )


def get_video_quiz(video: Video):
    """
    Retrieve the quiz associated with a given video.

    Args:
        video (Video): The video for which to retrieve the associated quiz.

    Returns:
        [Quiz | None]: The quiz associated with the video, or None if no quiz is found.
    """
    return Quiz.objects.filter(video=video).first()


def create_question_from_aristote_json(
    quiz: Quiz, question_type: str, question_dict: dict
) -> None:
    """
    Creates and associates questions with a given quiz based on JSON data.

    Args:
        quiz (Quiz): The quiz instance.
        questions_data (list): List of question data dictionaries.
    """
    title = question_dict["question"]
    explanation = question_dict["explanation"]
    start_timestamp = question_dict["answerPointer"]["startAnswerPointer"]
    end_timestamp = question_dict["answerPointer"]["stopAnswerPointer"]

    if question_type == "multiple_choice":
        question_choices = {
            i["optionText"]: i["correctAnswer"] for i in question_dict["choices"]
        }
        MultipleChoiceQuestion.objects.create(
            quiz=quiz,
            title=title,
            explanation=explanation,
            start_timestamp=time_to_seconds(start_timestamp),
            end_timestamp=time_to_seconds(end_timestamp),
            choices=json.dumps(question_choices),
        )


def import_quiz(video: Video, quiz_data_json: str):
    """
    function to import a quiz from a JSON input for a given video.

    Args:
        video (Video): The video for which to associate quiz.
        quiz_data_json (str): JSON string containing quiz data.
    """
    existing_quiz = get_video_quiz(video)
    if existing_quiz:
        existing_quiz.delete()
    quiz_data = json.loads(quiz_data_json)

    new_quiz = Quiz.objects.create(video=video)
    for question_type, question_list in quiz_data.items():
        for question in question_list:
            create_question_from_aristote_json(
                quiz=new_quiz, question_type=question_type, question_dict=question
            )


def calculate_question_score_from_form(question: Question, form) -> float:
    """
    Calculate the score for a given question and form.

    Args:
        question (Question): The question object.
        form: The form object containing the user's answers.

    Returns:
        float: The calculated score, a value between 0 and 1.
    """
    user_answer = None

    if question.get_type() == "single_choice":
        user_answer = form.cleaned_data.get("selected_choice")

    elif question.get_type() == "multiple_choice":
        user_answer = form.cleaned_data.get("selected_choice")
        if user_answer != "":
            user_answer = ast.literal_eval(
                user_answer
            )  # Cannot use JSON.loads in case of quotes in a user answer.

    elif question.get_type() == "short_answer":
        user_answer = form.cleaned_data.get("user_answer")

    # Add similar logic for other question types...

    return question.calculate_score(user_answer)
