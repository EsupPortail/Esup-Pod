from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .models import Recording
from pod.main.forms import add_placeholder_and_asterisk

DEFAULT_RECORDER_PATH = getattr(
    settings, 'DEFAULT_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)


class RecordingForm(forms.ModelForm):

    def __init__(self, request, *args, **kwargs):
        super(RecordingForm, self).__init__(*args, **kwargs)

        if not request.user.is_superuser:
            del self.fields['user']
            del self.fields['source_file']

        self.fields = add_placeholder_and_asterisk(self.fields)

        if self.initial.get("type"):
            self.fields['type'].widget = forms.HiddenInput()
        if self.initial.get("title") and self.initial.get("title") != "":
            self.fields['title'].widget = forms.HiddenInput()
        if self.initial.get("source_file"):
            self.fields['source_file'].widget = forms.HiddenInput()
        else:
            self.fields['source_file'] = forms.FilePathField(
                path=DEFAULT_RECORDER_PATH, recursive=True, label=_("source_file"))
            self.fields['source_file'].widget.attrs['class'] = 'form-control'

    class Meta:
        model = Recording
        exclude = ('comment', 'date_added')
