"""Handle the Advanced video search form."""

from django import forms
from pod.main.forms_utils import add_placeholder_and_asterisk
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import widgets


class SearchForm(forms.Form):
    """Handle the video advanced search form."""

    q = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(attrs={"type": "search"}),
    )
    start_date = forms.DateField(
        required=False,
        label=_("Start date"),
        widget=widgets.AdminDateWidget(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        required=False,
        label=_("End date"),
        widget=widgets.AdminDateWidget(attrs={"type": "date"}),
    )

    def __init__(self, *args, **kwargs) -> None:
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
