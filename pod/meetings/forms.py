from dataclasses import fields
from django.forms import ModelForm
from django import forms

from pod.meetings.models import Meetings


class MeetingsForm(ModelForm):
    class Meta:
        model = Meetings
        fields = ['titre', 'attendee_password', 'start_date', 'end_date', 'max_participants']

class JoinForm(forms.Form):
        name = forms.CharField(label="Your name")
        password = forms.CharField(
            widget=forms.PasswordInput(render_value=False))