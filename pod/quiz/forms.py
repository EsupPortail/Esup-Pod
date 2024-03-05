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

    title = forms.CharField(
        label=_("Title"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Your question")}),
    )
    explanation = forms.CharField(
        label=_("Explanation"),
        widget=forms.Textarea(
            attrs={
                "placeholder": _("Explanation of the question"),
                "cols": "40",
                "rows": "5",
            }
        ),
        required=False,
    )
    start_timestamp = forms.IntegerField(label=_("Start Timestamp"), required=False)
    end_timestamp = forms.IntegerField(label=_("End Timestamp"), required=False)
    type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        initial="unique_choice",
        widget=forms.Select(attrs={"class": "question-select-type"}),
        label=_("Question Type"),
        required=True,
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

    def clean(self):
        """
        Clean and validate the form data.

        Raises:
            ValidationError: If there are validation errors.
        """
        cleaned_data = super().clean()
        question_type = cleaned_data.get("type")

        if question_type == "unique_choice":
            choices_str = cleaned_data.get("unique_choice")
            try:
                choices = json.loads(choices_str)
            except json.JSONDecodeError:
                self.add_error(
                    "type", ValidationError(_("Invalid JSON format for choices."))
                )
                return cleaned_data

            # Check if there are at least 2 choices
            if len(choices) < 2:
                self.add_error(
                    "type",
                    ValidationError(
                        _("There must be at least 2 choices for a choice question.")
                    ),
                )
                return
            # Check if there is only one correct answer
            if sum([1 for choice in choices.values() if choice]) != 1:
                self.add_error(
                    "type",
                    ValidationError(
                        _(
                            "There must be only one correct answer for a unique choice question."
                        )
                    ),
                )
                return
        return cleaned_data


class QuizForm(forms.Form):
    """Form to add or edit a quiz."""

    connected_user_only = forms.BooleanField(
        label=_("Connected User Only"),
        required=False,
        widget=forms.CheckboxInput(),
        help_text=_("Only the connected users can answer to this quiz."),
    )
    show_correct_answers = forms.BooleanField(
        label=_("Show Correct Answers"),
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

    selected_choice = forms.CharField(widget=forms.RadioSelect(), required=False)

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

    class Meta:
        model = MultipleChoiceQuestion
        fields = ["choices"]
        widgets = {
            "choices": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        """Init multiple choice question form."""
        super(MultipleChoiceQuestionForm, self).__init__(*args, **kwargs)

        choices_str = self.instance.choices
        try:
            choices_dict = json.loads(choices_str)
        except json.JSONDecodeError:
            choices_dict = {}

        choices_list = [(choice, choice) for choice in choices_dict.keys()]

        self.fields["choices"].widget.choices = choices_list


class ShortAnswerQuestionForm(forms.ModelForm):
    """Form to add or edit a short answer question form."""

    user_answer = forms.CharField(widget=forms.TextInput(), required=False)

    class Meta:
        model = ShortAnswerQuestion
        fields = ["user_answer"]


class LongAnswerQuestionForm(forms.ModelForm):
    """Form to add or edit a long answer question form."""

    user_answer = forms.CharField(widget=forms.Textarea(), required=False)

    class Meta:
        model = LongAnswerQuestion
        fields = ["user_answer"]
