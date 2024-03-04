from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

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


def to_do(request):  # TODO remove this view
    return "To do..."


def create_quiz(request, video_slug: str):
    video = get_object_or_404(Video, slug=video_slug)
    question_formset_factory = formset_factory(QuestionForm, extra=2)
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
            "page_title": _(f"Quiz edition for the video: {video.title}"),
            "quiz_form": quiz_form,
            "question_formset": question_formset,
            "video": video,
        },
    )


def handle_post_request_for_create_or_edit_quiz(
    request, video: Video, question_formset_factory
):
    quiz_form = QuizForm(request.POST)
    question_formset = question_formset_factory(request.POST, prefix="questions")
    if quiz_form.is_valid() and question_formset.is_valid():
        connected_user_only = quiz_form.cleaned_data["connected_user_only"]
        show_correct_answers = quiz_form.cleaned_data["show_correct_answers"]

        new_quiz = Quiz(
            video=video,
            connected_user_only=connected_user_only,
            show_correct_answers=show_correct_answers,
        )
        new_quiz.save()

        for question_form in question_formset:
            # Check the type of question and create an instance accordingly
            question_type = question_form.cleaned_data.get("type")
            if question_type == "short_answer":
                ShortAnswerQuestion.objects.update_or_create(
                    quiz=new_quiz,
                    title=question_form.cleaned_data["title"],
                    explanation=question_form.cleaned_data["explanation"],
                    start_timestamp=question_form.cleaned_data["start_timestamp"],
                    end_timestamp=question_form.cleaned_data["end_timestamp"],
                    answer=question_form.cleaned_data["short_answer"],
                )
            elif question_type == "long_answer":
                LongAnswerQuestion.objects.update_or_create(
                    quiz=new_quiz,
                    title=question_form.cleaned_data["title"],
                    explanation=question_form.cleaned_data["explanation"],
                    start_timestamp=question_form.cleaned_data["start_timestamp"],
                    end_timestamp=question_form.cleaned_data["end_timestamp"],
                    answer=question_form.cleaned_data["long_answer"],
                )
            elif question_type == "unique_choice":
                UniqueChoiceQuestion.objects.update_or_create(
                    quiz=new_quiz,
                    title=question_form.cleaned_data["title"],
                    explanation=question_form.cleaned_data["explanation"],
                    start_timestamp=question_form.cleaned_data["start_timestamp"],
                    end_timestamp=question_form.cleaned_data["end_timestamp"],
                    choices=question_form.cleaned_data["unique_choice"],
                )

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


def video_quiz(request, video_slug: str):
    video = get_object_or_404(Video, slug=video_slug)
    quiz = get_video_quiz(video)
    form_submitted = False

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
        messages.success(request, f"Your score: {percentage_score:.2f}%")
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


def delete_quiz(request, video_slug: str):
    """Delete a quiz associated to a video."""
    video = get_object_or_404(Video, slug=video_slug)
    quiz = get_video_quiz(video)

    if quiz and (not (request.user.is_superuser or request.user.is_staff)):
        messages.add_message(
            request, messages.ERROR, _("You cannot delete this dressing.")
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
