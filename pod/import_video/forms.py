"""Forms for the Import_video module."""
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from pod.import_video.models import ExternalRecording
from pod.main.forms_utils import add_placeholder_and_asterisk
from pod.main.forms_utils import OwnerWidget, AddOwnerWidget


class ExternalRecordingForm(forms.ModelForm):
    """External recording form.

    Args:
        forms (ModelForm): model form

    Raises:
        ValidationError: owner of the recording cannot be an additional owner too
    """

    site = forms.ModelChoiceField(Site.objects.all(), required=False)
    is_admin = False
    is_superuser = False

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "type",
                    "source_url",
                    "start_at",
                    "owner",
                    "site",
                )
            },
        ),
    )

    def filter_fields_admin(form):
        """List fields, depends on user right."""
        if not form.is_superuser and not form.is_admin:
            form.remove_field("owner")
            form.remove_field("site")

    def clean(self):
        """Clean method."""
        cleaned_data = super(ExternalRecordingForm, self).clean()
        try:
            validator = URLValidator()
            validator(cleaned_data["source_url"])
        except ValidationError:
            self.add_error("source_url", _("Please enter a valid address"))

    def __init__(self, *args, **kwargs):
        """Initialize recording form."""
        self.is_staff = (
            kwargs.pop("is_staff") if "is_staff" in kwargs.keys() else self.is_staff
        )

        self.is_superuser = (
            kwargs.pop("is_superuser")
            if ("is_superuser" in kwargs.keys())
            else self.is_superuser
        )
        self.current_lang = kwargs.pop("current_lang", settings.LANGUAGE_CODE)
        self.current_user = kwargs.pop("current_user", None)

        super(ExternalRecordingForm, self).__init__(*args, **kwargs)

        self.set_queryset()
        self.filter_fields_admin()
        self.fields = add_placeholder_and_asterisk(self.fields)

        # We don't change the user who uploaded the record
        hidden_fields = ("uploaded_to_pod_by",)
        for field in hidden_fields:
            if self.fields.get(field, None):
                self.fields[field].widget = forms.HiddenInput()

    def remove_field(self, field):
        """Remove a field from the form."""
        if self.fields.get(field):
            del self.fields[field]

    def set_queryset(self):
        """Filter on owner."""
        if self.fields.get("owner"):
            self.fields["owner"].queryset = self.fields["owner"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )

    class Meta(object):
        """Metadata options.

        Args:
            object (class): internal class
        """

        model = ExternalRecording
        fields = "__all__"
        widgets = {
            "owner": OwnerWidget,
            "additional_owners": AddOwnerWidget,
        }
