from django import forms
from django.utils.translation import gettext_lazy as _

from pod.quiz.models import Question, Quiz, UniqueChoiceQuestion


# class QuestionForm(forms.ModelForm):
# QUESTION_TYPES = [
#     (
#         _("Redaction"),
#         [
#             ("short_answer", _("Short Answer")),
#             ("long_answer", _("Long Answer")),
#         ],
#     ),
#     (
#         _("Choice"),
#         [
#             ("unique_choice", _("Unique Choice")),
#             ("multiple_choice", _("Multiple Choice")),
#         ],
#     ),
# ]

#     type = forms.ChoiceField(
#         choices=QUESTION_TYPES,
#         initial="unique_choice",
#         widget=forms.Select(),
#         label=_("Question Type"),
#     )

#     class Meta:
#         model = Question
#         fields = ["title", "explanation", "start_timestamp", "end_timestamp", "type"]


# class ChoiceForm(forms.Form):
#     proposition = forms.CharField(label=_("Proposition"), max_length=255)
#     is_correct = forms.BooleanField(label=_("Is correct"), required=False)


# class UniqueChoiceForm(QuestionForm):
#     choices = forms.JSONField(
#         label=_("Choices"),
#         widget=forms.HiddenInput(),
#     )

#     ChoiceFormSet = forms.formset_factory(ChoiceForm, extra=2)

#     class Meta:
#         model = UniqueChoiceQuestion
#         fields = QuestionForm.Meta.fields + ["choices"]


# class ChoiceFormSet(forms.formset_factory(ChoiceForm, extra=2, can_delete=True)):
#     def clean(self):
#         cleaned_data = super().clean()
#         choices_dict = {}
#         for form in self.forms:
#             proposition = form.cleaned_data.get("proposition")
#             is_correct = form.cleaned_data.get("is_correct")
#             if proposition and is_correct:
#                 choices_dict[proposition] = is_correct
#         # if len(choices_dict) < 2:
#         #     raise forms.ValidationError(_("There must be at least 2 choices."))
#         # if sum(choices_dict.values()) != 1:
#         #     raise forms.ValidationError(_("There must be only one correct answer."))
#         return cleaned_data


# class QuizForm(forms.ModelForm):
#     QuestionFormSet = forms.formset_factory(UniqueChoiceForm, extra=2)

#     def __init__(self, *args, **kwargs):
#         self.video = kwargs.pop("video")
#         self.user = kwargs.pop("user")
#         super(QuizForm, self).__init__(*args, **kwargs)

#     class Meta:
#         model = Quiz
#         fields = ["connected_user_only", "activated_statistics", "show_correct_answers"]


class QuestionForm(forms.Form):
    QUESTION_TYPES = [
        (
            _("Redaction"),
            [
                ("short_answer", _("Short Answer")),
                ("long_answer", _("Long Answer")),
            ],
        ),
        (
            _("Choice"),
            [
                ("unique_choice", _("Unique Choice")),
            ],
        ),
    ]

    title = forms.CharField(label=_("Title"))
    explanation = forms.CharField(label=_("Explanation"))
    start_timestamp = forms.IntegerField(label=_("Start Timestamp"))
    end_timestamp = forms.IntegerField(label=_("End Timestamp"))
    type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        initial="unique_choice",
        widget=forms.Select(attrs={'class': 'question-select-type'}),
        label=_("Question Type"),
    )


class UniqueChoiceForm(forms.Form):
    choices = forms.JSONField(required=False)


class QuizForm(forms.Form):
    connected_user_only = forms.BooleanField(
        label=_("Connected User Only"), required=False)
    activated_statistics = forms.BooleanField(
        label=_("Activated Statistics"), required=False)
    show_correct_answers = forms.BooleanField(
        label=_("Show Correct Answers"), required=False)
