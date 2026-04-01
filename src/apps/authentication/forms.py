"""
Esup-Pod - Authentication forms.
"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _

from .models import GroupSite, Owner


class OwnerAdminForm(forms.ModelForm):
    """
    Form for managing Owner profiles in the administrative interface.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initializes the form."""
        super(OwnerAdminForm, self).__init__(*args, **kwargs)

    class Meta(object):
        """Owner form metadata."""

        model = Owner
        fields = "__all__"


class GroupSiteAdminForm(forms.ModelForm):
    """
    Form for linking groups to specific sites.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Standard form initialization."""
        super(GroupSiteAdminForm, self).__init__(*args, **kwargs)

    class Meta(object):
        """Meta."""

        model = GroupSite
        fields = "__all__"


class FrontOwnerForm(OwnerAdminForm):
    """
    User-facing form for updating basic profile information.
    """

    class Meta(object):
        """Meta."""

        model = Owner
        fields = ("userpicture",)


class AdminOwnerForm(forms.ModelForm):
    """
    Administrative form for Owner model with restricted fields.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Init."""
        super(AdminOwnerForm, self).__init__(*args, **kwargs)

    class Meta(object):
        """Meta."""

        model = Owner
        fields = []


class SetNotificationForm(forms.ModelForm):
    """Push notification preferences form."""

    def __init__(self, *args, **kwargs) -> None:
        """Init."""
        super(SetNotificationForm, self).__init__(*args, **kwargs)

    class Meta(object):
        """Meta."""

        model = Owner
        fields = ["accepts_notifications"]


User = get_user_model()


class GroupAdminForm(forms.ModelForm):
    """
    Form for managing standard Django groups with site-aware user filtering.
    """

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(_("Users"), False),
        label=_("Users"),
    )

    class Meta:
        """Meta."""

        model = Group
        fields = "__all__"
        exclude = []

    def __init__(self, *args, **kwargs) -> None:
        """Initializes the form and filters user choices by the current site."""
        super(GroupAdminForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["users"].initial = self.instance.user_set.all()
        self.fields["users"].queryset = self.fields["users"].queryset.filter(
            owner__sites=Site.objects.get_current()
        )

    def save_m2m(self) -> None:
        """Saves many-to-many relationship for users."""
        self.instance.user_set.set(self.cleaned_data["users"])

    def save(self, *args, **kwargs):
        """Saves the group and its linked users."""
        instance = super(GroupAdminForm, self).save()
        self.save_m2m()
        return instance
