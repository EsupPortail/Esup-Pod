from dataclasses import fields
from django.forms import ModelForm

from pod.meetings.models import Meetings


class MeetingsForm(ModelForm):
    class Meta:
        model = Meetings
        fields = ['titre', 'attendee_password', 'start_date', 'end_date', 'max_participants']