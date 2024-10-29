"""Esup-Pod speaker urls."""

from django.urls import path
from pod.speaker.views import speaker_management, add_speaker, get_jobs, get_speaker

app_name = "speaker"

urlpatterns = [
    path("", speaker_management, name="speaker_management"),
    path("add/", add_speaker, name="add_speaker"),
    path("get-speaker/<int:speaker_id>/", get_speaker, name="get_speaker"),
    path("get-jobs/<int:speaker_id>/", get_jobs, name="get_jobs"),
]
