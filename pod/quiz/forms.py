from django import forms
from django.utils.translation import gettext_lazy as _
from pod.main.forms_utils import add_placeholder_and_asterisk
from django.core.exceptions import ValidationError
import json


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

    title = forms.CharField(label=_("Title"), required=True, widget=forms.TextInput(attrs={'placeholder': _("Your question")}))
    explanation = forms.CharField(label=_("Explanation"),
                                  widget=forms.Textarea(attrs={'placeholder': _("Explanation of the question"), 'cols': '40', 'rows': '5'}), required=False)
    start_timestamp = forms.IntegerField(label=_("Start Timestamp"), required=False)
    end_timestamp = forms.IntegerField(label=_("End Timestamp"), required=False)
    type = forms.ChoiceField(
        choices=QUESTION_TYPES,
        initial="unique_choice",
        widget=forms.Select(attrs={'class': 'question-select-type'}),
        label=_("Question Type"),
        required=True
    )

    unique_choice = forms.CharField(widget=forms.HiddenInput(
        attrs={'class': 'hidden-unique-choice-field'}), required=False)
    short_answer = forms.CharField(widget=forms.HiddenInput(
        attrs={'class': 'hidden-short-answer-field'}), required=False, label=_("Short answer"))
    long_answer = forms.CharField(widget=forms.HiddenInput(
        attrs={'class': 'hidden-long-answer-field'}), required=False, label=_("Long answer"))

    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('type')

        if question_type == 'unique_choice':
            choices_str = cleaned_data.get('unique_choice')
            try:
                choices = json.loads(choices_str)
            except json.JSONDecodeError:
                self.add_error('type', ValidationError(_("Invalid JSON format for choices.")))
                return cleaned_data

            # Check if there are at least 2 choices
            if len(choices) < 2:
                self.add_error('type', ValidationError(_("There must be at least 2 choices for a choice question.")))
                return
            # Check if there is only one correct answer
            if sum([1 for choice in choices.values() if choice]) != 1:
                self.add_error('type', ValidationError(_("There must be only one correct answer for a unique choice question.")))
                return
        return cleaned_data


class QuizForm(forms.Form):
    connected_user_only = forms.BooleanField(
        label=_("Connected User Only"),
        required=False,
        widget=forms.CheckboxInput(),
        help_text=_("Only the connected users can answer to this quiz.")
    )
    show_correct_answers = forms.BooleanField(
        label=_("Show Correct Answers"),
        required=False,
        widget=forms.CheckboxInput(),
        help_text=_("The correction page can be reach.")
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        super(QuizForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
