"""Forms used in playlist application."""
from typing import Any, Mapping, Optional, Type, Union
from django import forms
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _

from pod.main.forms_utils import add_placeholder_and_asterisk

from .models import Playlist


class PlaylistForm(forms.ModelForm):
    """Form to add or edit a playlist."""

    class Meta:
        """Meta class."""
        model = Playlist
        fields = [
            "name",
            "description",
            "visibility",
            "password",
            "autoplay",
        ]

    name = forms.CharField(label=_("Name"), max_length=100)
    description = forms.CharField(label=_("Description"),
                                  widget=forms.Textarea, required=False)
    visibility = forms.ChoiceField(
        label=_("Visibility"), choices=Playlist.VISIBILITY_CHOICES)
    password = forms.CharField(
        label=_("Password"), widget=forms.PasswordInput, required=False)
    autoplay = forms.BooleanField(label=_("Autoplay"), required=False, initial=True)
    fieldsets = [
        (
            "general information",
            {
                "legend": f"<i class='bi bi-info-lg'></i>&nbsp;\
                    {_('General information')}",
                "fields": ["name", "description", "autoplay"],
            },
        ),
        (
            "security information",
            {
                "legend": f"<i class='bi bi-shield-lock'></i>&nbsp;\
                    {_('Security information')}",
                "fields": ["visibility", "password"],
            },
        ),
    ]

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        super(PlaylistForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)

    def clean_name(self):
        name = self.cleaned_data["name"]
        if name == "Favorites":
            raise forms.ValidationError(_('You cannot create a playlist named "Favorites"'))
        return name


class PlaylistRemoveForm(forms.Form):
    """Form to remove a playlist."""
    agree = forms.BooleanField(
        label=_("I agree"),
        help_text=_("Remove playlist cannot be undone"),
        widget=forms.CheckboxInput(),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        super(PlaylistRemoveForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
