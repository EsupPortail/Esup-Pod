from dataclasses import fields
import datetime
from django.forms import ModelForm, ValidationError
from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models.query import QuerySet
from django.contrib.admin import widgets

from pod.meetings.models import Meetings, User

class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'

class MeetingsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.is_staff = (
            kwargs.pop("is_staff") if "is_staff" in kwargs.keys() else self.is_staff
        )
        self.is_superuser = (
            kwargs.pop("is_superuser")
            if ("is_superuser" in kwargs.keys())
            else self.is_superuser
        )

        super(MeetingsForm, self).__init__(*args, **kwargs)

        if self.fields.get("meeting"):
            self.fields["meeting"].label = ("File")
        if self.fields.get("owner"):
            self.fields["owner"].queryset = self.fields["owner"].queryset.filter(
                owner__sites=Site.objects.get_current()
            )

    class Meta:
        model = Meetings
        fields = ['name', 'attendeePW', 'moderatorPW', 'start_date', 'end_date', 'max_participants', 'auto_start_recording', 'allow_start_stop_recording', 'lock_settings_disable_cam', 'lock_settings_disable_mic', 'lock_settings_disable_private_chat', 'lock_settings_disable_public_chat', 'lock_settings_disable_note', 'lock_settings_locked_layout', 'ask_password']
        widgets = {
            'start_date':DateTimeInput(),
            'end_date':DateTimeInput(),
        }

class MeetingsJoinForm(forms.Form):
    fullName = forms.CharField(label="Your name")
    password = forms.CharField(label= ("Password"), widget=forms.PasswordInput())