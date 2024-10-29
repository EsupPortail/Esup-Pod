"""Esup-Pod Video completion urls."""

from django.urls import re_path
from .views import video_completion
from .views import video_caption_maker
from .views import video_completion_contributor
from .views import video_completion_speaker
from .views import video_completion_document
from .views import video_completion_track
from .views import video_completion_overlay

app_name = "completion"

urlpatterns = [
    re_path(
        r"^caption_maker/(?P<slug>[\-\d\w]+)/$",
        video_caption_maker,
        name="video_caption_maker",
    ),
    re_path(
        r"^contributor/(?P<slug>[\-\d\w]+)/$",
        video_completion_contributor,
        name="video_completion_contributor",
    ),
    re_path(
        r"^speaker/(?P<slug>[\-\d\w]+)/$",
        video_completion_speaker,
        name="video_completion_speaker",
    ),
    re_path(
        r"^document/(?P<slug>[\-\d\w]+)/$",
        video_completion_document,
        name="video_completion_document",
    ),
    re_path(
        r"^track/(?P<slug>[\-\d\w]+)/$",
        video_completion_track,
        name="video_completion_track",
    ),
    re_path(
        r"^overlay/(?P<slug>[\-\d\w]+)/$",
        video_completion_overlay,
        name="video_completion_overlay",
    ),
    re_path(
        r"^(?P<slug>[\-\d\w]+)/$",
        video_completion,
        name="video_completion",
    ),
]
