"""Esup-Pod forms speaker."""

from django_select2 import forms as s2forms
from django.utils.translation import gettext_lazy as _
from django import forms
from django.forms.widgets import HiddenInput
from .models import Speaker, Job, JobVideo
from pod.main.forms_utils import add_placeholder_and_asterisk
from django.conf import settings


class JobWidget(s2forms.ModelSelect2Widget):
    """Widget for selecting speaker job."""

    search_fields = [
        "title__icontains",
        "speaker__lastname__icontains",
        "speaker__firstname__icontains",
    ]


class SpeakerForm(forms.ModelForm):
    """Speaker form fields."""

    class Meta:
        model = Speaker
        fields = ["firstname", "lastname"]

    def __init__(self, *args, **kwargs):
        """Init method."""
        super(SpeakerForm, self).__init__(*args, **kwargs)
        if not getattr(settings, "REQUIRED_SPEAKER_FIRSTNAME", False):
            self.fields["firstname"].required = False
        self.fields = add_placeholder_and_asterisk(self.fields)


class JobForm(forms.ModelForm):
    """Job form fields."""

    class Meta:
        model = Job
        fields = ["title"]


class JobVideoForm(forms.ModelForm):
    """VideoJob form fields."""

    def __init__(self, *args, **kwargs):
        """Initialize fields."""
        super(JobVideoForm, self).__init__(*args, **kwargs)
        self.fields["video"].widget = HiddenInput()
        self.fields["job"].queryset = Job.objects.all()

    class Meta(object):
        """Set form Metadata."""

        model = JobVideo
        widgets = {
            "job": JobWidget(
                attrs={
                    "data-placeholder": _(
                        "You can search speaker by first name, last name and job."
                    ),
                    "class": "w-100",
                }
            )
        }
        fields = "__all__"
