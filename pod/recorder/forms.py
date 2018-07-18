from django import forms

from .models import Recording
from pod.main.forms import add_placeholder_and_asterisk


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

    class Meta:
        model = Recording
        exclude = ('comment', 'date_added')
