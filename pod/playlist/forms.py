"""Forms used in playlist application."""
from django import forms
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _

from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.meeting.forms import AddOwnerWidget

from .apps import FAVORITE_PLAYLIST_NAME
from .models import Playlist

general_informations = _('General informations')
security_informations = _('Security informations')


class PlaylistForm(forms.ModelForm):
    """Form to add or edit a playlist."""

    class Meta:
        """Meta class."""
        model = Playlist
        exclude = [
            "editable",
            "slug",
            "owner",
            "date_created",
            "date_updated",
        ]
        widgets = {
            "additional_owners": AddOwnerWidget,
        }

    field_order = [
        "name",
        "description",
        "visibility",
        "promoted",
        "password",
        "autoplay",
        "additional_owners",
    ]
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={"autocomplete": "off"}
        ),
        required=False,
        help_text=_("Please choose a password if this playlist is password-protected."),
    )
    promoted = forms.BooleanField(
        label=_("Promoted"),
        required=False,
        help_text=_("Selecting this setting causes your playlist to be promoted on the page"
                    + " listing promoted public playlists. However, if this setting is deactivated,"
                    + " your playlist will still be accessible to everyone."
                    + "<br>For general use, we recommend that you leave this setting disabled."),
    )
    fieldsets = [
        (
            "general informations",
            {
                "legend": f"<i class='bi bi-info-lg'></i>&nbsp;\
                    {general_informations}",
                "fields": ["name", "description", "autoplay"],
            },
        ),
        (
            "security informations",
            {
                "legend": f"<i class='bi bi-shield-lock'></i>&nbsp;\
                    {security_informations}",
                "fields": ["additional_owners", "visibility", "password", "promoted"],
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
        if name == FAVORITE_PLAYLIST_NAME:
            raise forms.ValidationError(
                _(f'You cannot create a playlist named "{FAVORITE_PLAYLIST_NAME}"')
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


class PlaylistPasswordForm(forms.Form):
    """Form to access to a password-protected playlist."""
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        """Init method."""
        super(PlaylistPasswordForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
