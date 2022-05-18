from dataclasses import fields
from django.forms import ModelForm
from django import forms

from pod.meetings.models import Meetings


class MeetingsForm(ModelForm):
    class Meta:
        model = Meetings
        fields = ['name', 'attendee_password', 'start_date', 'end_date', 'max_participants']
        
class JoinForm(forms.Form):
    name = forms.CharField(label="Your name")
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False))

class MeetingsDeleteForm(forms.Form):
    agree = forms.BooleanField(
        label=("I agree"),
        help_text=("Delete meeting cannot be undo"),
        widget=forms.CheckboxInput(),
    )