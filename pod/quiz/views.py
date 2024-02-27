from django.forms import formset_factory
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from pod.quiz.forms import QuestionForm, QuizForm
from pod.video.models import Video


def to_do(request):  # TODO remove this view
    return "To do..."


def create_quiz(request, video_slug: str):
    video = get_object_or_404(Video, slug=video_slug)
    QuestionFormSet = formset_factory(QuestionForm, extra=2)
    if request.method == 'POST':
        quiz_form = QuizForm(request.POST)
        question_formset = QuestionFormSet(request.POST, prefix='questions')

    else:
        quiz_form = QuizForm()
        question_formset = QuestionFormSet(prefix='questions')

    return render(request, 'quiz/create_edit_quiz.html', {
        "page_title": _(f"Quiz edition for the video: {video.title}"),
        'quiz_form': quiz_form,
        'question_formset': question_formset,
        'video': video,
    })
