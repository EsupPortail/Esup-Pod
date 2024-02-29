from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pod.quiz.forms import QuestionForm, QuizForm
from pod.quiz.models import LongAnswerQuestion, Quiz, ShortAnswerQuestion, UniqueChoiceQuestion
from pod.video.models import Video
from django.contrib import messages


def to_do(request):  # TODO remove this view
    return "To do..."


def create_quiz(request, video_slug: str):
    video = get_object_or_404(Video, slug=video_slug)
    question_formset_factory = formset_factory(QuestionForm, extra=2)
    if request.method == 'POST':
        print("POST request received")
        return handle_post_request_for_create_or_edit_quiz(request, video, question_formset_factory)
    else:
        quiz_form = QuizForm()
        question_formset = question_formset_factory(prefix='questions')

    return render(request, 'quiz/create_edit_quiz.html', {
        "page_title": _(f"Quiz edition for the video: {video.title}"),
        'quiz_form': quiz_form,
        'question_formset': question_formset,
        'video': video,
    })


def handle_post_request_for_create_or_edit_quiz(request, video: Video, question_formset_factory):
    quiz_form = QuizForm(request.POST)
    question_formset = question_formset_factory(request.POST, prefix='questions')
    if quiz_form.is_valid() and question_formset.is_valid():
        connected_user_only = quiz_form.cleaned_data['connected_user_only']
        show_correct_answers = quiz_form.cleaned_data['show_correct_answers']

        new_quiz = Quiz(
            video=video,
            connected_user_only=connected_user_only,
            show_correct_answers=show_correct_answers,
        )
        # new_quiz.save()

        for question_form in question_formset:
            # Check the type of question and create an instance accordingly
            question_type = question_form.cleaned_data.get('type')
            qu = None
            if question_type == 'short_answer':
                qu = ShortAnswerQuestion(
                    quiz=new_quiz,
                    title=question_form.cleaned_data['title'],
                    explanation=question_form.cleaned_data['explanation'],
                    start_timestamp=question_form.cleaned_data['start_timestamp'],
                    end_timestamp=question_form.cleaned_data['end_timestamp'],
                    answer=question_form.cleaned_data['short_answer'],
                )
            elif question_type == 'long_answer':
                qu = LongAnswerQuestion(
                    title=question_form.cleaned_data['title'],
                    explanation=question_form.cleaned_data['explanation'],
                    start_timestamp=question_form.cleaned_data['start_timestamp'],
                    end_timestamp=question_form.cleaned_data['end_timestamp'],
                    answer=question_form.cleaned_data['long_answer'],
                )
            elif question_type == 'unique_choice':
                qu = UniqueChoiceQuestion(
                    quiz=new_quiz,
                    title=question_form.cleaned_data['title'],
                    explanation=question_form.cleaned_data['explanation'],
                    start_timestamp=question_form.cleaned_data['start_timestamp'],
                    end_timestamp=question_form.cleaned_data['end_timestamp'],
                    choices=question_form.cleaned_data['unique_choice'],
                )

        messages.add_message(
            request,
            messages.SUCCESS,
            _("Quiz successfully created."),
        )

        return HttpResponseRedirect(
            reverse("video:video", kwargs={"slug": video.slug})
        )
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("The data sent to create the quiz are invalid."),
        )
    return render(
        request,
        'quiz/create_edit_quiz.html',
        {
            "page_title": _(f"Quiz edition for the video: {video.title}"),
            'quiz_form': quiz_form,
            'question_formset': question_formset,
            'video': video,
        })
