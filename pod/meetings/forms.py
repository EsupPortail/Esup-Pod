from dataclasses import fields
from django.forms import ModelForm
from django import forms

from pod.meetings.models import Meetings


class MeetingsForm(ModelForm):
    class Meta:
        model = Meetings
        fields = ['name', 'attendee_password', 'start_date', 'end_date', 'max_participants', 'auto_start_recording', 'allow_start_stop_recording', 'lock_settings_disable_cam', 'lock_settings_disable_mic', 'lock_settings_disable_private_chat', 'lock_settings_disable_public_chat', 'lock_settings_disable_note', 'lock_settings_locked_layout', 'ask_password']
        
class JoinForm(forms.Form):
    name = forms.CharField(label="Your name")
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False))

