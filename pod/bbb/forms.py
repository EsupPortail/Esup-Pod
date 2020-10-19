from django import forms
from django.conf import settings
from .models import Meeting
from pod.main.forms import add_placeholder_and_asterisk

USE_BBB = getattr(settings, 'USE_BBB', False)


class MeetingForm(forms.ModelForm):

    def __init__(self, request, *args, **kwargs):
        super(MeetingForm, self).__init__(*args, **kwargs)

        # All fields are hidden. This form is like a Confirm prompt
        self.fields = add_placeholder_and_asterisk(self.fields)
        self.fields['meeting_id'].widget = forms.HiddenInput()
        self.fields['internal_meeting_id'].widget = forms.HiddenInput()
        self.fields['meeting_name'].widget = forms.HiddenInput()
        self.fields['date'].widget = forms.HiddenInput()
        self.fields['encoding_step'].widget = forms.HiddenInput()
        self.fields['recorded'].widget = forms.HiddenInput()
        self.fields['recording_available'].widget = forms.HiddenInput()
        self.fields['recording_url'].widget = forms.HiddenInput()
        self.fields['thumbnail_url'].widget = forms.HiddenInput()
        self.fields['encoded_by'].widget = forms.HiddenInput()

    class Meta:
        model = Meeting
        exclude = ()
