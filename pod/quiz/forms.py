from django import forms
from django.utils.translation import gettext_lazy as _
from pod.main.forms_utils import add_placeholder_and_asterisk


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
