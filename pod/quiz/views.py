"""Esup-Pod quiz views."""

import ast
import json
from typing import Optional
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from pod.main.views import in_maintenance

from pod.quiz.forms import QuestionForm, QuizDeleteForm, QuizForm
from pod.quiz.models import (
    LongAnswerQuestion,
    MultipleChoiceQuestion,
    Question,
    Quiz,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)
from pod.quiz.utils import get_video_quiz
from pod.video.models import Video
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

from pod.video_encode_transcript.utils import time_to_seconds


@csrf_protect
@login_required(redirect_field_name="referrer")
def create_quiz(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """
    View function for creating a quiz associated with a video.

    Args:
        request (WSGIRequest): The HTTP request.
        video_slug (str): The slug of the associated video.

    Raises:
        PermissionDenied: If the user lacks the required privileges.

    Returns:
        HttpResponse: The HTTP response for rendering the quiz creation form.
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    video = get_object_or_404(Video, slug=video_slug)
    if get_video_quiz(video):
        return redirect(reverse("quiz:edit_quiz", kwargs={"video_slug": video.slug}))

    question_formset_factory = formset_factory(QuestionForm, extra=2)
    if not (
        request.user.is_superuser or request.user.is_staff or request.user == video.owner
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot create a quiz for this video.")
        )
        raise PermissionDenied

    if request.method == "POST":
        return handle_post_request_for_create_or_edit_quiz(
            request, video, question_formset_factory, action="create"
        )
    else:
        quiz_form = QuizForm()
        question_formset = question_formset_factory(prefix="questions")

    return render(
        request,
        "quiz/create_edit_quiz.html",
        {
            "page_title": _("Quiz creation for the video “%s”") % video.title,
            "quiz_form": quiz_form,
            "question_formset": question_formset,
            "video": video,
        },
    )


def update_questions(existing_quiz: Quiz, question_formset) -> None:
    """
    Updates existing questions in a given quiz based on the provided formset.

    Args:
        existing_quiz (Quiz): The existing quiz instance.
        question_formset: The formset containing updated question data.
    """
    for question_form, existing_question in zip(
        question_formset, existing_quiz.get_questions()
    ):
        question_type = question_form.cleaned_data.get("type")
        title = question_form.cleaned_data["title"]
        explanation = question_form.cleaned_data["explanation"]
        start_timestamp = question_form.cleaned_data["start_timestamp"]
        end_timestamp = question_form.cleaned_data["end_timestamp"]

        if question_type == "short_answer":
            existing_question.answer = question_form.cleaned_data["short_answer"]
        elif question_type == "long_answer":
            existing_question.answer = question_form.cleaned_data["long_answer"]
        elif question_type == "single_choice":
            existing_question.choices = question_form.cleaned_data["single_choice"]
        elif question_type == "multiple_choice":
            existing_question.choices = question_form.cleaned_data["multiple_choice"]

        existing_question.title = title
        existing_question.explanation = explanation
        existing_question.start_timestamp = start_timestamp
        existing_question.end_timestamp = end_timestamp

        existing_question.save()


def handle_post_request_for_create_or_edit_quiz(
    request: WSGIRequest, video: Video, question_formset_factory, action: str
) -> HttpResponse:
    """
    Handles the POST request for creating or editing a quiz associated with a video.

    Args:
        request (WSGIRequest): The HTTP request.
        video (Video): The associated video instance.
        question_formset_factory: The formset factory for handling question forms.
        action (str): The action to perform - "create" or "edit".

    Returns:
        HttpResponse: The HTTP response for rendering the appropriate template.
    """
    quiz_form = QuizForm(request.POST)
    question_formset = question_formset_factory(request.POST, prefix="questions")
    if quiz_form.is_valid() and question_formset.is_valid():
        if action == "create":
            new_quiz = create_or_edit_quiz_instance(video, quiz_form, action)
            create_questions(new_quiz, question_formset)
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Quiz successfully created."),
            )
        elif action == "edit":
            new_quiz = create_or_edit_quiz_instance(video, quiz_form, action)
            update_questions(new_quiz, question_formset)
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Quiz successfully updated."),
            )

        return HttpResponseRedirect(reverse("video:video", kwargs={"slug": video.slug}))
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("The data sent to create the quiz are invalid."),
        )

    return render(
        request,
        "quiz/create_edit_quiz.html",
        {
            "page_title": _(f"Quiz edition for the video: {video.title}"),
            "quiz_form": quiz_form,
            "question_formset": question_formset,
            "video": video,
        },
    )


def create_or_edit_quiz_instance(
    video: Video, quiz_form: QuizForm, action: str
) -> Optional[Quiz]:
    """
    Creates a new quiz instance or updates an existing one based on the provided action.

    Args:
        video (Video): The associated video instance.
        quiz_form (QuizForm): The form containing quiz data.
        action (str): The action to perform - "create" or "edit".

    Returns:
        Optional[Quiz]: The created or updated quiz instance, or None if the action is invalid.
    """
    if action == "create":
        return Quiz.objects.create(
            video=video,
            connected_user_only=quiz_form.cleaned_data["connected_user_only"],
            show_correct_answers=quiz_form.cleaned_data["show_correct_answers"],
        )
    elif action == "edit":
        existing_quiz = get_object_or_404(Quiz, video=video)
        existing_quiz.connected_user_only = quiz_form.cleaned_data["connected_user_only"]
        existing_quiz.show_correct_answers = quiz_form.cleaned_data[
            "show_correct_answers"
        ]
        existing_quiz.save()
        return existing_quiz


def create_questions(new_quiz: Quiz, question_formset) -> None:
    """
    Creates and associates questions with a given quiz based on the provided formset.

    Args:
        new_quiz (Quiz): The newly created quiz instance.
        question_formset: The formset containing question data.
    """
    for question_form in question_formset:
        question_type = question_form.cleaned_data.get("type")
        title = question_form.cleaned_data["title"]
        explanation = question_form.cleaned_data["explanation"]
        start_timestamp = question_form.cleaned_data["start_timestamp"]
        end_timestamp = question_form.cleaned_data["end_timestamp"]

        if question_type == "short_answer":
            ShortAnswerQuestion.objects.get_or_create(
                quiz=new_quiz,
                title=title,
                explanation=explanation,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                answer=question_form.cleaned_data["short_answer"],
            )
        elif question_type == "long_answer":
            LongAnswerQuestion.objects.get_or_create(
                quiz=new_quiz,
                title=title,
                explanation=explanation,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                answer=question_form.cleaned_data["long_answer"],
            )
        elif question_type == "single_choice":
            SingleChoiceQuestion.objects.get_or_create(
                quiz=new_quiz,
                title=title,
                explanation=explanation,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                choices=question_form.cleaned_data["single_choice"],
            )
        elif question_type == "multiple_choice":
            MultipleChoiceQuestion.objects.get_or_create(
                quiz=new_quiz,
                title=title,
                explanation=explanation,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                choices=question_form.cleaned_data["multiple_choice"],
            )


def calculate_score(question: Question, form) -> float:
    """
    Calculate the score for a given question and form.

    Args:
        question (Question): The question object.
        form: The form object containing the user's answers.

    Returns:
        float: The calculated score, a value between 0 and 1.
    """
    user_answer = None
    correct_answer = None
    if question.get_type() == "single_choice":
        user_answer = form.cleaned_data.get("selected_choice")
        correct_answer = question.get_answer()

    elif question.get_type() == "multiple_choice":
        user_answer = form.cleaned_data.get("selected_choice")
        correct_answer = question.get_answer()
        if user_answer != "":
            user_answer = ast.literal_eval(
                user_answer
            )  # Cannot use JSON.loads in case of quotes in a user answer.
            intersection = set(user_answer) & set(correct_answer)
            score = len(intersection) / len(correct_answer)
            return score

    elif question.get_type() in {"short_answer", "long_answer"}:
        user_answer = form.cleaned_data.get("user_answer")
        correct_answer = question.get_answer()

    # Add similar logic for other question types...

    if (user_answer is not None and user_answer != "") and correct_answer is not None:
        return 1.0 if user_answer.lower() == correct_answer.lower() else 0.0

    return 0.0


def process_quiz_submission(request: WSGIRequest, quiz: Quiz) -> float:
    """
    Process the submission of a quiz and calculate the user's percentage score.

    Args:
        request (WSGIRequest): The HTTP request object.
        quiz (Quiz): The quiz object.

    Returns:
        float: The percentage score based on correct answers, ranging from 0 to 100.
    """
    total_questions = len(quiz.get_questions())
    score = 0.0

    for question in quiz.get_questions():
        form = question.get_question_form(request.POST)
        if form.is_valid():
            score += calculate_score(question, form)

    percentage_score = (score / total_questions) * 100
    return percentage_score


def video_quiz(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """
    View function for rendering a quiz associated with a video.

    Args:
        request (WSGIRequest): The HTTP request.
        video_slug (str): The slug of the video.

    Returns:
        HttpResponse: The HTTP response.
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    video = get_object_or_404(Video, slug=video_slug)
    quiz = get_video_quiz(video)
    form_submitted = False
    percentage_score = None

    if quiz.connected_user_only and not request.user.is_authenticated:
        return redirect("%s?referrer=%s" % (settings.LOGIN_URL, request.get_full_path()))

    if request.method == "POST":
        percentage_score = process_quiz_submission(request, quiz)
        form_submitted = True

    return render(
        request,
        "quiz/video_quiz.html",
        {
            "page_title": _("Quiz for the video “%s”") % video.title,
            "video": video,
            "quiz": quiz,
            "form_submitted": form_submitted,
            "percentage_score": percentage_score,
        },
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def delete_quiz(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """
    View function for rendering the quiz deletion page for a given video.

    Args:
        request (WSGIRequest): The HTTP request.
        video_slug (str): The slug of the video.

    Returns:
        HttpResponse: The HTTP response.
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    video = get_object_or_404(Video, slug=video_slug)
    quiz = get_object_or_404(Quiz, video=video)

    if quiz and not (
        request.user.is_superuser or request.user.is_staff or request.user == video.owner
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot delete the quiz for this video.")
        )
        raise PermissionDenied

    form = QuizDeleteForm()

    if request.method == "POST":
        form = QuizDeleteForm(request.POST)
        if form.is_valid():
            quiz.delete()
            messages.add_message(request, messages.INFO, _("The quiz has been deleted."))
            return redirect(reverse("video:video", kwargs={"slug": video.slug}))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "quiz/delete_quiz.html",
        {
            "page_title": _("Deleting the quiz for the video “%s”") % video.title,
            "quiz": quiz,
            "video": video,
            "form": form,
        },
    )


# EDIT


@csrf_protect
@login_required(redirect_field_name="referrer")
def edit_quiz(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """
    View function for rendering the quiz editing page for a given video.

    Args:
        request (WSGIRequest): The HTTP request.
        video_slug (str): The slug of the video.

    Returns:
        HttpResponse: The HTTP response.
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    video = get_object_or_404(Video, slug=video_slug)
    question_formset_factory = formset_factory(QuestionForm, extra=0)

    if not (
        request.user.is_superuser or request.user.is_staff or request.user == video.owner
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this quiz."))
        raise PermissionDenied

    quiz = get_object_or_404(Quiz, video=video)

    if request.method == "POST":
        return handle_post_request_for_create_or_edit_quiz(
            request, video, question_formset_factory, action="edit"
        )
    else:
        quiz_form = QuizForm(
            initial={
                "connected_user_only": quiz.connected_user_only,
                "show_correct_answers": quiz.show_correct_answers,
            }
        )

        existing_questions = quiz.get_questions()
        initial_data = get_initial_data(existing_questions=existing_questions)

        question_formset = question_formset_factory(
            prefix="questions",
            initial=[
                {
                    "type": question.get_type(),
                    "title": question.title,
                    "explanation": question.explanation,
                    "start_timestamp": question.start_timestamp,
                    "end_timestamp": question.end_timestamp,
                }
                for question in existing_questions
            ],
        )

    return render(
        request,
        "quiz/create_edit_quiz.html",
        {
            "page_title": _("Quiz edition for the video “%s”") % video.title,
            "quiz_form": quiz_form,
            "question_formset": question_formset,
            "video": video,
            "initial_data": initial_data,
        },
    )


def get_initial_data(existing_questions=None) -> str:
    """
    Generate initial data for JavaScript based on existing questions.

    Args:
        existing_questions (list): List of existing question objects.

    Returns:
        str: JSON-encoded initial data for JavaScript fields.
    """
    if existing_questions:
        initial_data = {
            "existing_questions": [
                {
                    "short_answer": (
                        question.answer if question.get_type() == "short_answer" else None
                    ),
                    "long_answer": (
                        question.answer if question.get_type() == "long_answer" else None
                    ),
                    "choices": (
                        json.loads(question.choices)
                        if question.get_type() in {"single_choice", "multiple_choice"}
                        else None
                    ),
                    # Add other datas needed for JS fields
                }
                for question in existing_questions
            ],
        }
    return json.dumps(initial_data)


@csrf_protect
@login_required(redirect_field_name="referrer")
def import_quiz(request: WSGIRequest, video_slug: str, quiz_data_json: str):
    """
    View function to import a quiz from a JSON input for a given video.

    Args:
        request (WSGIRequest): The HTTP request.
        video_slug (str): The slug of the associated video.
        quiz_data_json (str): JSON string containing quiz data.

    Raises:
        PermissionDenied: If the user lacks the required privileges.

    Returns:
        HttpResponse: The HTTP response indicating the result of the import.
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    video = get_object_or_404(Video, slug=video_slug)

    if not (request.user.is_superuser or request.user.is_staff or request.user == video.owner):
        messages.add_message(
            request, messages.ERROR, _("You cannot import a quiz for this video.")
        )
        raise PermissionDenied

    existing_quiz = get_video_quiz(video)
    if existing_quiz:
        existing_quiz.delete()
    quiz_data = json.loads(quiz_data_json)

    new_quiz = Quiz.objects.create(video=video)
    for question_type, question_list in quiz_data.items():
        for question in question_list:
            create_question_from_aristote_json(quiz=new_quiz, question_type=question_type, question_dict=question)


def create_question_from_aristote_json(quiz: Quiz, question_type: str, question_dict: dict) -> None:
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
        question_choices = {i["optionText"]: i["correctAnswer"] for i in question_dict["choices"]}
        MultipleChoiceQuestion.objects.create(
            quiz=quiz,
            title=title,
            explanation=explanation,
            start_timestamp=time_to_seconds(start_timestamp),
            end_timestamp=time_to_seconds(end_timestamp),
            choices=json.dumps(question_choices),
        )
