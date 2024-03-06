"""Esup-Pod quiz views."""

import json
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
    Quiz,
    ShortAnswerQuestion,
    UniqueChoiceQuestion,
)
from pod.quiz.utils import get_video_quiz
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
            request, video, question_formset_factory
        )
    else:
        quiz_form = QuizForm()
        question_formset = question_formset_factory(prefix="questions")

    return render(
        request,
        "quiz/create_edit_quiz.html",
        {
            "page_title": _(f"Quiz creation for the video: {video.title}"),
            "quiz_form": quiz_form,
            "question_formset": question_formset,
            "video": video,
        },
    )


def handle_post_request_for_create_or_edit_quiz(
    request: WSGIRequest, video: Video, question_formset_factory
) -> HttpResponse:
    """
    Handles the POST request for creating or editing a quiz associated with a video.

    Args:
        request (WSGIRequest): The HTTP request.
        video (Video): The associated video instance.
        question_formset_factory: The formset factory for handling question forms.

    Returns:
        HttpResponse: The HTTP response for rendering the appropriate template.
    """
    quiz_form = QuizForm(request.POST)
    question_formset = question_formset_factory(request.POST, prefix="questions")

    if quiz_form.is_valid() and question_formset.is_valid():
        new_quiz = create_quiz_instance(video, quiz_form)
        create_questions(new_quiz, question_formset)

        messages.add_message(
            request,
            messages.SUCCESS,
            _("Quiz successfully created."),
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


def create_quiz_instance(video: Video, quiz_form: QuizForm) -> Quiz:
    """
    Creates a new quiz instance based on the provided video and quiz form.

    Args:
        video (Video): The associated video instance.
        quiz_form (QuizForm): The form containing quiz data.

    Returns:
        Quiz: The created quiz instance.
    """
    return Quiz.objects.create(
        video=video,
        connected_user_only=quiz_form.cleaned_data["connected_user_only"],
        show_correct_answers=quiz_form.cleaned_data["show_correct_answers"],
    )


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
        elif question_type == "unique_choice":
            UniqueChoiceQuestion.objects.get_or_create(
                quiz=new_quiz,
                title=title,
                explanation=explanation,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                choices=question_form.cleaned_data["unique_choice"],
            )


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
    if quiz.connected_user_only and not request.user.is_authenticated:
        return redirect("%s?referrer=%s" % (settings.LOGIN_URL, request.get_full_path()))

    if request.method == "POST":
        total_questions = len(quiz.get_questions())
        score = 0

        for question in quiz.get_questions():
            form = question.get_question_form(request.POST)
            if form.is_valid():
                if isinstance(question, UniqueChoiceQuestion):
                    user_answer = form.cleaned_data.get("selected_choice")
                    correct_answer = question.get_answer()
                    is_correct = user_answer == correct_answer

                    if is_correct:
                        score += 1

                elif isinstance(question, MultipleChoiceQuestion):
                    user_answers = form.cleaned_data.get("user_answer")
                    correct_answers = question.get_answer()
                    is_correct = user_answers == correct_answers

                    if is_correct:
                        score += 1

                elif isinstance(question, ShortAnswerQuestion) or isinstance(
                    question, LongAnswerQuestion
                ):
                    user_answer = form.cleaned_data.get("user_answer")
                    correct_answer = question.get_answer()
                    is_correct = user_answer.lower() == correct_answer.lower()

                    if is_correct:
                        score += 1

                # Add similar logic for other question types...

        percentage_score = (score / total_questions) * 100
        messages.success(request, _("Your score is: %.2f%%") % percentage_score)
        form_submitted = True

    return render(
        request,
        "quiz/video_quiz.html",
        {
            "page_title": _(f"Quiz for the video: {video.title}"),
            "video": video,
            "quiz": quiz,
            "form_submitted": form_submitted,
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
    quiz = get_video_quiz(video)

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
            request, video, question_formset_factory, quiz=quiz
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
            "page_title": _(f"Quiz edition for the video: {video.title}"),
            "quiz_form": quiz_form,
            "question_formset": question_formset,
            "video": video,
            "initial_data": initial_data,
        },
    )


def get_initial_data(existing_questions=None):
    if existing_questions:
        initial_data = {
            "existing_questions": [
                {
                    "short_answer": question.answer
                    if question.get_type() == "short_answer"
                    else None,
                    "long_answer": question.answer
                    if question.get_type() == "long_answer"
                    else None,
                    "choices": json.loads(question.choices)
                    if question.get_type() == "unique_choice"
                    else None,
                    # Ajoutez d'autres données nécessaires pour les champs JS
                }
                for question in existing_questions
            ],
        }
    return json.dumps(initial_data)
