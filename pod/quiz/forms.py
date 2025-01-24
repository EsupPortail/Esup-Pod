"""Esup-Pod quiz forms."""

from django import forms
from django.utils.translation import gettext_lazy as _
from pod.main.forms_utils import add_placeholder_and_asterisk
from django.core.exceptions import ValidationError
import json

from pod.quiz.models import (
    MultipleChoiceQuestion,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)


class QuestionForm(forms.Form):
    """Form to add or edit a question."""

    QUESTION_TYPES = [
        (
            _("Redaction"),
            [
                ("short_answer", _("Short answer")),
            ],
        ),
        (
            _("Choice"),
            [
                ("single_choice", _("Single choice")),
                ("multiple_choice", _("Multiple choice")),
            ],
        ),
    ]

    title = forms.CharField(
        label=_("Title"),
        required=True,
        widget=forms.TextInput(attrs={"placeholder": _("Your question")}),
        help_text=_("Please choose a title between 1 and %(max)s characters.")
        % {"max": 250},
    )
    explanation = forms.CharField(
        label=_("Explanation"),
        widget=forms.Textarea(
            attrs={
                "placeholder": _("Explanation of the answer."),
            }
        ),
        required=False,
        help_text=_(
            "An explanation that will be displayed once the user has responded (feedback)."
        ),
    )
    start_timestamp = forms.IntegerField(
        label=_("Start timestamp"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "start-timestamp-field"}),
        help_text=_("The start time of the answer in the video (in seconds)."),
    )
    end_timestamp = forms.IntegerField(
        label=_("End timestamp"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "end-timestamp-field"}),
        help_text=_("The end time of the answer in the video (in seconds)."),
    )
    type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        initial="single_choice",
        widget=forms.Select(attrs={"class": "question-select-type"}),
        label=_("Question type"),
        required=True,
        help_text=_("Please choose the question type."),
    )
    question_id = forms.UUIDField(
        widget=forms.HiddenInput(),
        required=False,
    )
    single_choice = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "hidden-single-choice-field"}),
        required=False,
        label=_("Single choice"),
    )
    short_answer = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "hidden-short-answer-field"}),
        required=False,
        label=_("Short answer"),
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

        if question_type == "single_choice":
            self._clean_single_choice()
        elif question_type == "multiple_choice":
            self._clean_multiple_choice()
        return cleaned_data

    def __init__(self, *args, **kwargs) -> None:
        """Init question form."""
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)

    def _clean_single_choice(self) -> None:
        """Call SingleChoiceQuestion's clean method."""
        choices_str = self.cleaned_data.get("single_choice")
        single_choice_question = SingleChoiceQuestion(choices=choices_str)
        try:
            single_choice_question.clean()
        except ValidationError as e:
            for error in e.error_list:
                self.add_error("single_choice", error)

    def _clean_multiple_choice(self) -> None:
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

    is_draft = forms.BooleanField(
        label=_("Draft"),
        widget=forms.CheckboxInput(),
        required=False,
        help_text=_(
            "If this box is checked, "
            "the quiz will be visible and accessible only by you "
            "and the additional owners."
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init quiz form."""
        super(QuizForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class QuizDeleteForm(forms.Form):
    """Form to delete a quiz."""

    agree = forms.BooleanField(
        label=_("I agree"),
        required=True,
        help_text=_("Delete video quiz cannot be undone"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init deletion quiz form."""
        super(QuizDeleteForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


# TYPES FORMS


class SingleChoiceQuestionForm(forms.ModelForm):
    """Form to show a single choice question form."""

    selected_choice = forms.CharField(
        label=_("Single choice question"),
        widget=forms.RadioSelect(),
        required=True,
        help_text=_("Please choose one answer."),
    )

    class Meta:
        """SingleChoiceQuestionForm Metadata."""

        model = SingleChoiceQuestion
        fields = ["selected_choice"]

    def __init__(self, *args, **kwargs) -> None:
        """Init single choice question form."""
        super(SingleChoiceQuestionForm, self).__init__(*args, **kwargs)

        choices_str = self.instance.choices
        try:
            choices_dict = json.loads(choices_str)
        except json.JSONDecodeError:
            choices_dict = {}

        choices_list = [(choice, choice) for choice in choices_dict.keys()]
        self.fields["selected_choice"].widget.choices = choices_list
        self.fields["selected_choice"].widget.wrap_label = False
        self.fields["selected_choice"].widget.attrs["class"] = "list-unstyled ps-2 mb-0"

    def clean_selected_choice(self):
        data = self.cleaned_data["selected_choice"]
        return data


class MultipleChoiceQuestionForm(forms.ModelForm):
    """Form to show a multiple choice question form."""

    selected_choice = forms.CharField(
        label=_("Multiple choice question"),
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        help_text=_("Please check any answers you want."),
    )

    class Meta:
        model = MultipleChoiceQuestion
        fields = ["selected_choice"]

    def __init__(self, *args, **kwargs) -> None:
        """Init multiple choice question form."""
        super(MultipleChoiceQuestionForm, self).__init__(*args, **kwargs)

        choices_str = self.instance.choices
        try:
            choices_dict = json.loads(choices_str)
        except json.JSONDecodeError:
            choices_dict = {}

        choices_list = [(choice, choice) for choice in choices_dict.keys()]

        self.fields["selected_choice"].widget.choices = choices_list
        self.fields["selected_choice"].widget.attrs["class"] = "list-unstyled ps-2 mb-0"

    def clean_selected_choice(self):
        data = self.cleaned_data["selected_choice"]
        return data


class ShortAnswerQuestionForm(forms.ModelForm):
    """Form to show a short answer question form."""

    user_answer = forms.CharField(
        label=_("Short answer question"),
        widget=forms.TextInput(),
        required=True,
        help_text=_("Write a short answer."),
    )

    class Meta:
        model = ShortAnswerQuestion
        fields = ["user_answer"]

    def __init__(self, *args, **kwargs) -> None:
        """Init short answer question form."""
        super(ShortAnswerQuestionForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
