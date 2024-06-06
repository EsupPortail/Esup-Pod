from django import forms
from .models import Speaker, Job


class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = ['firstname', 'lastname']


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title']
