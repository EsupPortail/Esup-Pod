import os
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import Recording
from pod.main.forms import add_placeholder_and_asterisk

DEFAULT_MEDIACOURSE_RECORDER_PATH = getattr(
    settings, 'DEFAULT_MEDIACOURSE_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)

class RecordingForm(forms.ModelForm):

    def __init__(self, request, *args, **kwargs):
        super(RecordingForm, self).__init__(*args, **kwargs)

        self.fields = add_placeholder_and_asterisk(self.fields)

        self.fields['mediapath'] = forms.FilePathField(
            path=DEFAULT_MEDIACOURSE_RECORDER_PATH,
            recursive=True,
            match=".*\.*$",
            label=_("Source file in MP4 or ZIP format (mediapath)")
        )

        # Type depends on extension of the mediapath
        self.fields['mediapath'].widget.attrs['class'] = 'form-control'
        self.fields['type'].widget = forms.HiddenInput()

        # Superuser has more rights
        if not request.user.is_superuser:
            self.fields['mediapath'].widget = forms.HiddenInput()
            self.fields['recorder'].widget = forms.HiddenInput()

    def clean_type(self):
        instance = getattr(self, 'instance', None)
        return self.cleaned_data['type']

    class Meta:
        model = Recording
        exclude = ('comment',)