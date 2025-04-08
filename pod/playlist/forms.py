"""Esup-Pod playlist application forms."""

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.meeting.forms import AddOwnerWidget

from .apps import FAVORITE_PLAYLIST_NAME
from .models import Playlist

USE_PROMOTED_PLAYLIST = getattr(settings, "USE_PROMOTED_PLAYLIST", False)
RESTRICT_PROMOTED_PLAYLIST_ACCESS_TO_STAFF_ONLY = getattr(
    settings,
    "RESTRICT_PROMOTED_PLAYLIST_ACCESS_TO_STAFF_ONLY",
    False,
)

general_informations = _("General informations")
security_informations = _("Security informations")


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
            "site",
        ]
        if not USE_PROMOTED_PLAYLIST:
            exclude.append("promoted")
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
    name = forms.CharField(
        label=_("Title"),
        widget=forms.TextInput(
            attrs={
                "aria-describedby": "id_nameHelp",
            },
        ),
        help_text=_("Please choose a title between 1 and %(max)s characters.")
        % {"max": 250},
    )
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(
            attrs={
                "aria-describedby": "id_descriptionHelp",
            },
        ),
        required=False,
        help_text=_("Please choose a description. This description is empty by default."),
    )
    visibility = forms.ChoiceField(
        label=_("Right of access"),
        widget=forms.Select(
            attrs={
                "aria-describedby": "id_visibilityHelp",
            },
        ),
        choices=Playlist.VISIBILITY_CHOICES,
        help_text=_(
            "Please choose an access right among “public”, “password-protected”, “private”."
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "off",
                "aria-describedby": "id_passwordHelp",
            },
        ),
        required=False,
        help_text=_("Please choose a password if this playlist is password-protected."),
    )
    if USE_PROMOTED_PLAYLIST:
        promoted = forms.BooleanField(
            label=_("Promoted"),
            widget=forms.CheckboxInput(
                attrs={
                    "aria-describedby": "id_promotedHelp",
                },
            ),
            required=False,
            help_text=_(
                "Selecting this setting causes your playlist to be promoted on the page"
                + " listing promoted public playlists. However, if this setting is deactivated,"
                + " your playlist will still be accessible to everyone."
                + "<br>For general use, we recommend that you leave this setting disabled."
            ),
        )
    autoplay = forms.BooleanField(
        label=_("Autoplay"),
        widget=forms.CheckboxInput(
            attrs={
                "aria-describedby": "id_autoplayHelp",
            },
        ),
        required=False,
        help_text=_("Please choose if this playlist is an autoplay playlist or not."),
    )
    fieldsets = [
        (
            "general informations",
            {
                "legend": f"<i class='bi bi-info-lg' aria-hidden='true'></i>&nbsp;\
                    {general_informations}",
                "fields": ["name", "description", "autoplay"],
            },
        ),
        (
            "security informations",
            {
                "legend": f"<i class='bi bi-shield-lock' aria-hidden='true'></i>&nbsp;\
                    {security_informations}",
                "fields": ["additional_owners", "visibility", "password", "promoted"],
            },
        ),
    ]

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        self.user = kwargs.pop("user", None)
        super(PlaylistForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
        if self.user:
            if (
                RESTRICT_PROMOTED_PLAYLIST_ACCESS_TO_STAFF_ONLY or self.user.is_superuser
            ) and "promoted" in self.fields:
                del self.fields["promoted"]
        else:
            if "promoted" in self.fields:
                del self.fields["promoted"]

    def clean_name(self) -> str:
        """Check if the playlist name asked is correct."""
        name = self.cleaned_data["name"]
        if name == FAVORITE_PLAYLIST_NAME:
            raise forms.ValidationError(
                _("You cannot create a playlist named “%(name)s”")
                % {"name": FAVORITE_PLAYLIST_NAME}
            )
        return name

    def clean_add_owner(self, cleaned_data) -> None:
        """Check if the owner is correct."""
        if "additional_owners" in cleaned_data.keys() and isinstance(
            self.cleaned_data["additional_owners"], QuerySet
        ):
            playlist_owner = (
                self.instance.owner
                if hasattr(self.instance, "owner")
                else (
                    cleaned_data["owner"]
                    if "owner" in cleaned_data.keys()
                    else self.current_user
                )
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
        widget=forms.CheckboxInput(
            attrs={
                "aria-describedby": "id_agreeHelp",
            },
        ),
    )

    def __init__(self, *args, **kwargs) -> None:
        """Init method."""
        super(PlaylistRemoveForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)


class PlaylistPasswordForm(forms.Form):
    """Form to access to a password-protected playlist."""

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(
            attrs={
                "aria-describedby": "id_passwordHelp",
            },
        ),
        help_text=_(
            "This playlist is protected by password, please fill in and click send."
        ),
    )

    def __init__(self, *args, **kwargs):
        """Init method."""
        super(PlaylistPasswordForm, self).__init__(*args, **kwargs)
        self.fields = add_placeholder_and_asterisk(self.fields)
