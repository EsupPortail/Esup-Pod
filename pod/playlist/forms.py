from typing import Any, Dict, Mapping, Optional, Type, Union
from django import forms
from django.contrib.sites.models import Site
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from django.utils.translation import ugettext_lazy as _

from pod.main.forms_utils import add_placeholder_and_asterisk

from .models import Playlist


class PlaylistForm(forms.ModelForm):
    class Meta:
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
                "legend": f"<i class='bi bi-info-lg'></i>&nbsp;{_('General information')}",
                "fields": ["name", "description", "autoplay"],
            },
        ),
        (
            "security information",
            {
                "legend": f"<i class='bi bi-shield-lock'></i>&nbsp;{_('Security information')}",
                "fields": ["visibility", "password"],
            },
        ),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super(PlaylistForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
