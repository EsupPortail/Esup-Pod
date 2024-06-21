"""Esup-Pod forms speaker."""

from django_select2 import forms as s2forms
from django import forms
from django.forms.widgets import HiddenInput
from .models import Speaker, Job, JobVideo


class JobWidget(s2forms.ModelSelect2Widget):
    """Widget for selecting speaker job."""

    search_fields = [
        "title__icontains", "speaker__lastname__icontains",
    ]


class SpeakerForm(forms.ModelForm):
    """Speaker form fields."""

    class Meta:
        model = Speaker
        fields = ['firstname', 'lastname']


class JobForm(forms.ModelForm):
    """Job form fields."""

    class Meta:
        model = Job
        fields = ['title']


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
        widgets = {"job": JobWidget}
        fields = "__all__"
