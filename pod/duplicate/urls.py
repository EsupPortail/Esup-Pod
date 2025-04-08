"""Esup-Pod duplicate urls."""

from django.urls import path
from pod.duplicate.views import video_duplicate

app_name = "duplicate"

urlpatterns = [
    path("<slug:slug>/", video_duplicate, name="video_duplicate"),
]
