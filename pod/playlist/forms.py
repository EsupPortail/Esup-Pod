"""Forms used in playlist application."""
from typing import Any, Mapping, Optional, Type, Union
from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _

from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.meeting.forms import AddOwnerWidget

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
            "additional_owners",
        ]

    name = forms.CharField(
        label=_("Name"),
        max_length=250,
        help_text=_("Please choose a name between 1 and 250 characters."),
    )
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea,
        required=False,
        help_text=_("Please choose a description. This description is empty by default."),
    )
    visibility = forms.ChoiceField(
        label=_("Visibility"),
        choices=Playlist.VISIBILITY_CHOICES,
        help_text=_("Please chosse an visibility among 'public', 'protected', 'private'."),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
        required=False,
        help_text=_("Please choose a password if this playlist is protected."),
    )
    autoplay = forms.BooleanField(
        label=_("Autoplay"),
        required=False,
        initial=True,
        help_text=_("Please choose if this playlist is an autoplay playlist or not."),
    )
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
                "fields": ["additional_owners", "visibility", "password"],
            },
        ),
    ]

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        super(PlaylistForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


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
