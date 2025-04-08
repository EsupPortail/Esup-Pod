"""Esup-Pod quiz views."""

import ast
import json
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_protect
from pod.main.views import in_maintenance

from pod.quiz.forms import QuestionForm, QuizDeleteForm, QuizForm
from pod.quiz.models import (
    MultipleChoiceQuestion,
    Question,
    Quiz,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)
from pod.quiz.utils import calculate_question_score_from_form, get_video_quiz
from pod.video.models import Video
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest


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

    question_formset_factory = formset_factory(QuestionForm, extra=1)
    if not (
        request.user.is_superuser or request.user.is_staff or request.user == video.owner
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot create a quiz for this video.")
        )
        raise PermissionDenied

    if request.method == "POST":
        question_formset = question_formset_factory(
            request.POST,
            prefix="questions",
        )
        quiz_form = handle_post_request_for_create_or_edit_quiz(
            request, video, question_formset, action="create"
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
    Update existing questions in a given quiz based on the provided formset.

    Args:
        existing_quiz (Quiz): The existing quiz instance.
        question_formset: The formset containing updated question data.
    """
    for question_form in question_formset:
        question_type = question_form.cleaned_data.get("type")
        question_id = question_form.cleaned_data.get("question_id")
        if question_id:
            existing_question = get_question(question_type, question_id, existing_quiz)
            if existing_question:
                if not question_form.cleaned_data[question_type]:
                    raise ValidationError(
                        _("No answer defined for question %s.") % question_id
                    )
                update_question(existing_question, question_form.cleaned_data)
        elif not question_form.cleaned_data.get("DELETE"):
            create_question(
                question_type=question_type,
                quiz=existing_quiz,
                title=question_form.cleaned_data["title"],
                explanation=question_form.cleaned_data["explanation"],
                start_timestamp=question_form.cleaned_data["start_timestamp"],
                end_timestamp=question_form.cleaned_data["end_timestamp"],
                question_data=question_form.cleaned_data[question_type],
            )


def update_question(existing_question: Question, cleaned_data) -> None:
    """
    Update existing question in a given quiz based on the provided form data.

    Args:
        existing_question (Question): The existing quiz instance.
        cleaned_data: The updated question data.
    """
    if cleaned_data.get("DELETE"):
        existing_question.delete()
    else:
        question_type = cleaned_data.get("type")
        existing_question.title = cleaned_data["title"]
        existing_question.explanation = cleaned_data["explanation"]
        existing_question.start_timestamp = cleaned_data["start_timestamp"]
        existing_question.end_timestamp = cleaned_data["end_timestamp"]
        if question_type in {"short_answer"}:
            existing_question.answer = cleaned_data[question_type]
        elif question_type in {"single_choice", "multiple_choice"}:
            existing_question.choices = cleaned_data[question_type]
        existing_question.save()


def handle_post_request_for_create_or_edit_quiz(
    request: WSGIRequest, video: Video, question_formset, action: str
) -> QuizForm:
    """
    Handle the POST request for creating or editing a quiz associated with a video.

    Args:
        request (WSGIRequest): The HTTP request.
        video (Video): The associated video instance.
        question_formset: The formset factory for handling question forms.
        action (str): The action to perform - "create" or "edit".

    Returns:
        QuizForm: The HTTP response for rendering the appropriate template.
    """
    quiz_form = QuizForm(request.POST)
    if quiz_form.is_valid() and question_formset.is_valid():

        if action == "create":
            new_quiz = create_or_edit_quiz_instance(video, quiz_form, action)
            if new_quiz:
                create_questions(new_quiz, question_formset)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("Quiz successfully created."),
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Error during quiz creation."),
                )
        elif action == "edit":
            new_quiz = create_or_edit_quiz_instance(video, quiz_form, action)
            if new_quiz:
                update_questions(new_quiz, question_formset)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("Quiz successfully updated."),
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Error during quiz update."),
                )
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("The data sent to create the quiz are invalid."),
        )

    return quiz_form


def get_question(question_type: str, question_id: int, quiz: Quiz):
    """
    Returns the question found according to its type, identifier and the quiz to which it belongs.

    Args:
        question_type (str): The type fo the question.
        question_id (int): The identifier of the question.
        quiz (Quiz): The quiz object.

    Returns:
        question: The question if found else None.
    """
    question = None
    if question_type == "short_answer":
        question = ShortAnswerQuestion.objects.filter(
            quiz=quiz,
            id=question_id,
        ).first()
    elif question_type == "single_choice":
        question = SingleChoiceQuestion.objects.filter(
            quiz=quiz,
            id=question_id,
        ).first()
    elif question_type == "multiple_choice":
        question = MultipleChoiceQuestion.objects.filter(
            quiz=quiz,
            id=question_id,
        ).first()
    return question


def create_or_edit_quiz_instance(video: Video, quiz_form: QuizForm, action: str):
    """
    Create a new quiz instance or update an existing one based on the provided action.

    Args:
        video (Video): The associated video instance.
        quiz_form (QuizForm): The form containing quiz data.
        action (str): The action to perform - "create" or "edit".

    Returns:
        [Quiz | None]: The created or updated quiz instance, or None if the action is invalid.
    """
    if action == "create":
        return Quiz.objects.create(
            video=video,
            connected_user_only=quiz_form.cleaned_data["connected_user_only"],
            show_correct_answers=quiz_form.cleaned_data["show_correct_answers"],
            is_draft=quiz_form.cleaned_data["is_draft"],
        )
    elif action == "edit":
        existing_quiz = get_object_or_404(Quiz, video=video)
        existing_quiz.connected_user_only = quiz_form.cleaned_data["connected_user_only"]
        existing_quiz.show_correct_answers = quiz_form.cleaned_data[
            "show_correct_answers"
        ]
        existing_quiz.is_draft = quiz_form.cleaned_data["is_draft"]
        existing_quiz.save()
        return existing_quiz


def create_question(
    question_type: str,
    quiz: Quiz,
    title: str,
    explanation: str,
    start_timestamp: int,
    end_timestamp: int,
    question_data: str,
):
    if question_type == "short_answer":
        ShortAnswerQuestion.objects.get_or_create(
            quiz=quiz,
            title=title,
            explanation=explanation,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            answer=question_data,
        )
    elif question_type == "single_choice":
        SingleChoiceQuestion.objects.get_or_create(
            quiz=quiz,
            title=title,
            explanation=explanation,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            choices=question_data,
        )
    elif question_type == "multiple_choice":
        MultipleChoiceQuestion.objects.get_or_create(
            quiz=quiz,
            title=title,
            explanation=explanation,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            choices=question_data,
        )


def create_questions(new_quiz: Quiz, question_formset) -> None:
    """
    Create and associate questions with a given quiz based on the provided formset.

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

        create_question(
            question_type=question_type,
            quiz=new_quiz,
            title=title,
            explanation=explanation,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            question_data=question_form.cleaned_data[question_type],
        )


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
    questions_stats = {}
    questions_answers = {}
    questions_form_errors = {}
    for question in quiz.get_questions():
        form = question.get_question_form(request.POST)
        if form.is_valid():
            question_score = calculate_question_score_from_form(question, form)
            score += question_score
            questions_stats[question.id] = question_score
            if question.get_type() in ["single_choice", "multiple_choice"]:
                user_answer = form.cleaned_data["selected_choice"]
                if question.get_type() == "multiple_choice":
                    user_answer = ast.literal_eval(user_answer)
                correct_answer = question.get_answer()
                questions_answers["question_%s" % question.id] = [
                    user_answer,
                    correct_answer,
                ]
            elif question.get_type() in {"short_answer"}:
                user_answer = form.cleaned_data.get("user_answer")
                correct_answer = question.get_answer()
                questions_answers["question_%s" % question.id] = [
                    user_answer,
                    correct_answer,
                ]
        else:
            questions_form_errors[question.title] = _(
                "You have to choose at least one answer"
            )
    percentage_score = (score / total_questions) * 100
    return percentage_score, questions_stats, questions_answers, questions_form_errors


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
    questions_stats = {}
    questions_answers = {}
    questions_form_errors = {}

    if quiz.is_draft and (video.owner != request.user):
        raise Http404()

    if quiz.connected_user_only and not request.user.is_authenticated:
        return redirect("%s?referrer=%s" % (settings.LOGIN_URL, request.get_full_path()))

    if request.method == "POST":
        (percentage_score, questions_stats, questions_answers, questions_form_errors) = (
            process_quiz_submission(request, quiz)
        )
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
            "questions_stats": questions_stats,
            "questions_answers": questions_answers,
            "questions_form_errors": questions_form_errors,
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
            return redirect(
                reverse("video:completion:video_completion", kwargs={"slug": video.slug})
            )
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
    if not (
        request.user.is_superuser or request.user.is_staff or request.user == video.owner
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this quiz."))
        raise PermissionDenied

    quiz = get_object_or_404(Quiz, video=video)
    existing_questions = quiz.get_questions()
    if existing_questions != []:
        initial_data = get_initial_data(existing_questions)
    else:
        initial_data = None
    extra = 2 if existing_questions == [] else 0
    question_formset_factory = formset_factory(QuestionForm, extra=extra, can_delete=True)
    if request.method == "POST":
        question_formset = question_formset_factory(
            request.POST,
            prefix="questions",
            initial=[
                {
                    "type": question.get_type(),
                    "title": question.title,
                    "explanation": question.explanation,
                    "start_timestamp": question.start_timestamp,
                    "end_timestamp": question.end_timestamp,
                    "question_id": question.id,
                }
                for question in existing_questions
            ],
        )
        quiz_form = handle_post_request_for_create_or_edit_quiz(
            request, video, question_formset, action="edit"
        )
    else:
        quiz_form = QuizForm(
            initial={
                "connected_user_only": quiz.connected_user_only,
                "show_correct_answers": quiz.show_correct_answers,
                "is_draft": quiz.is_draft,
            }
        )

        question_formset = question_formset_factory(
            prefix="questions",
            initial=[
                {
                    "type": question.get_type(),
                    "title": question.title,
                    "explanation": question.explanation,
                    "start_timestamp": question.start_timestamp,
                    "end_timestamp": question.end_timestamp,
                    "question_id": question.id,
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
    initial_data = {}
    if existing_questions:
        initial_data = {
            "existing_questions": [
                {
                    "short_answer": (
                        question.answer if question.get_type() == "short_answer" else None
                    ),
                    "choices": (
                        json.loads(question.get_choices())
                        if question.get_type() in {"single_choice", "multiple_choice"}
                        else None
                    ),
                    # Add other datas needed for JS fields
                }
                for question in existing_questions
            ],
        }
        return json.dumps(initial_data)
    else:
        return None
