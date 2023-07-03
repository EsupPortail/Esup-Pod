"""Forms used in playlist application."""
from django import forms
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
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
        widgets = {
            "additional_owners": AddOwnerWidget,
        }

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
        help_text=_(
            '''
            Please chosse an visibility among 'public', 'protected', 'private'.
            '''
        ),
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

    def clean_name(self):
        """Method to check if the playlist name asked is correct."""
        name = self.cleaned_data["name"]
        if name == "Favorites":
            raise forms.ValidationError(
                _('You cannot create a playlist named "Favorites"')
            )
        return name

    def clean_add_owner(self, cleaned_data):
        """Method to check if the owner is correct."""
        if "additional_owners" in cleaned_data.keys() and isinstance(
            self.cleaned_data["additional_owners"], QuerySet
        ):
            playlist_owner = (
                self.instance.owner
                if hasattr(self.instance, "owner")
                else cleaned_data["owner"]
                if "owner" in cleaned_data.keys()
                else self.current_user
            )
            if (
                playlist_owner
                and playlist_owner in self.cleaned_data["additional_owners"].all()
            ):
                raise ValidationError(
                    _("Owner of the video cannot be an additional owner too")
                )


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
