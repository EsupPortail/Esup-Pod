"""Esup-Pod cut urls."""

from django.urls import path
from pod.cut.views import cut_video

app_name = "cut"

urlpatterns = [
    path("<slug:slug>/", cut_video, name="video_cut"),
]
