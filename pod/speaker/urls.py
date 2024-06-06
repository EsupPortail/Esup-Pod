"""Esup-Pod speaker urls."""

from django.urls import path
from pod.speaker.views import speaker_management, add_speaker

app_name = "speaker"

urlpatterns = [
    path("", speaker_management, name="speaker_management"),
    path("add/", add_speaker, name='add_speaker'),
]
