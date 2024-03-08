"""Esup-Pod quiz forms."""

from django import forms
from django.utils.translation import gettext_lazy as _
from pod.main.forms_utils import add_placeholder_and_asterisk
from django.core.exceptions import ValidationError
import json

from pod.quiz.models import (
    LongAnswerQuestion,
    MultipleChoiceQuestion,
    ShortAnswerQuestion,
    UniqueChoiceQuestion,
)


class QuestionForm(forms.Form):
    """Form to add or edit a question."""

    QUESTION_TYPES = [
        (
            _("Redaction"),
            [
                ("short_answer", _("Short answer")),
                ("long_answer", _("Long answer")),
            ],
        ),
        (
            _("Choice"),
            [
                ("unique_choice", _("Unique choice")),
                ("multiple_choice", _("Multiple choice")),
            ],
        ),
    ]

    title = forms.CharField(
        label=_("Title"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Your question")}),
        help_text=_("Please choose a title between 1 and 250 characters."),
    )
    explanation = forms.CharField(
        label=_("Explanation"),
        widget=forms.Textarea(
            attrs={
                "placeholder": _("Explanation of the question"),
            }
        ),
        required=False,
        help_text=_("Please choose an explanation."),
    )
    start_timestamp = forms.IntegerField(
        label=_("Start timestamp"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "start-timestamp-field"}),
        help_text=_("Please choose the beginning time of the answer in the video (in seconds)."),
    )
    end_timestamp = forms.IntegerField(
        label=_("End timestamp"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "end-timestamp-field"}),
        help_text=_("Please choose the end time of the answer in the video (in seconds)."),
    )
    type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        initial="unique_choice",
        widget=forms.Select(attrs={"class": "question-select-type"}),
        label=_("Question Type"),
        required=True,
        help_text=_("Please choose the question type."),
    )

    unique_choice = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "hidden-unique-choice-field"}),
        required=False,
        label=_("Unique choice"),
    )
    short_answer = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "hidden-short-answer-field"}),
        required=False,
        label=_("Short answer"),
    )
    long_answer = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "hidden-long-answer-field"}),
        required=False,
        label=_("Long answer"),
    )
    multiple_choice = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "hidden-multiple-choice-field"}),
        required=False,
        label=_("Multiple choice"),
    )
    # Add other question types

    def clean(self):
        """
        Clean and validate the form data.

        Raises:
            ValidationError: If there are validation errors.
        """
        cleaned_data = super().clean()
        question_type = cleaned_data.get("type")

        if question_type == "unique_choice":
            self._clean_unique_choice()
        elif question_type == "multiple_choice":
            self._clean_multiple_choice()
        return cleaned_data

    def __init__(self, *args, **kwargs) -> None:
        """Init question form."""
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)

    def _clean_unique_choice(self):
        """Call UniqueChoiceQuestion's clean method."""
        choices_str = self.cleaned_data.get("unique_choice")
        unique_choice_question = UniqueChoiceQuestion(choices=choices_str)
        try:
            unique_choice_question.clean()
        except ValidationError as e:
            for error in e.error_list:
                self.add_error("unique_choice", error)

    def _clean_multiple_choice(self):
        """Call MultipleChoiceQuestion's clean method."""
        choices_str = self.cleaned_data.get("multiple_choice")
        multiple_choice_question = MultipleChoiceQuestion(choices=choices_str)
        try:
            multiple_choice_question.clean()
        except ValidationError as e:
            for error in e.error_list:
                self.add_error("multiple_choice", error)


class QuizForm(forms.Form):
    """Form to add or edit a quiz."""

    connected_user_only = forms.BooleanField(
        label=_("Connected user only"),
        required=False,
        widget=forms.CheckboxInput(),
        help_text=_("Only the connected users can answer to this quiz."),
    )
    show_correct_answers = forms.BooleanField(
        label=_("Show correct answers"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(),
        help_text=_("The correction page can be reach."),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init quiz form."""
        super(QuizForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class QuizDeleteForm(forms.Form):
    """Form to delete a quiz."""

    agree = forms.BooleanField(
        label=_("I agree"),
        help_text=_("Delete video quiz cannot be undone"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs):
        """Init deletion quiz form."""
        super(QuizDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


# TYPES FORMS


class UniqueChoiceQuestionForm(forms.ModelForm):
    """Form to add or edit a unique choice question form."""

    selected_choice = forms.CharField(
        label=_("Unique choice question"),
        widget=forms.RadioSelect(),
        required=False,
        help_text=_("Please choose one answer."),
    )

    class Meta:
        model = UniqueChoiceQuestion
        fields = ["selected_choice"]

    def __init__(self, *args, **kwargs):
        """Init unique choice question form."""
        super(UniqueChoiceQuestionForm, self).__init__(*args, **kwargs)

        choices_str = self.instance.choices
        try:
            choices_dict = json.loads(choices_str)
        except json.JSONDecodeError:
            choices_dict = {}

        choices_list = [(choice, choice) for choice in choices_dict.keys()]

        self.fields["selected_choice"].widget.choices = choices_list


class MultipleChoiceQuestionForm(forms.ModelForm):
    """Form to add or edit a multiple choice question form."""

    selected_choice = forms.CharField(
        label=_("Multiple choice question"),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text=_("Please check any answers you want."),
    )

    class Meta:
        model = MultipleChoiceQuestion
        fields = ["selected_choice"]

    def __init__(self, *args, **kwargs):
        """Init multiple choice question form."""
        super(MultipleChoiceQuestionForm, self).__init__(*args, **kwargs)

        choices_str = self.instance.choices
        try:
            choices_dict = json.loads(choices_str)
        except json.JSONDecodeError:
            choices_dict = {}

        choices_list = [(choice, choice) for choice in choices_dict.keys()]

        self.fields["selected_choice"].widget.choices = choices_list


class ShortAnswerQuestionForm(forms.ModelForm):
    """Form to add or edit a short answer question form."""

    user_answer = forms.CharField(
        label=_("Short answer question"),
        widget=forms.TextInput(),
        required=False,
        help_text=_("Write a short answer."),
    )

    class Meta:
        model = ShortAnswerQuestion
        fields = ["user_answer"]

    def __init__(self, *args, **kwargs) -> None:
        """Init short answer question form."""
        super(ShortAnswerQuestionForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class LongAnswerQuestionForm(forms.ModelForm):
    """Form to add or edit a long answer question form."""

    user_answer = forms.CharField(
        label=_("Long answer question"),
        widget=forms.Textarea(),
        required=False,
        help_text=_("Write a long answer."),
    )

    class Meta:
        model = LongAnswerQuestion
        fields = ["user_answer"]

    def __init__(self, *args, **kwargs) -> None:
        """Init short answer question form."""
        super(LongAnswerQuestionForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
