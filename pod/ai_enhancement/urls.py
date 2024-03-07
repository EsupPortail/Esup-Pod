"""URL patterns used in ai_enhancement application."""
from django.urls import path

from pod.ai_enhancement.views import (
    enrich_subtitles,
    enrich_video,
    enrich_video_json,
    toggle_webhook,
)

app_name = "ai_enhancement"

urlpatterns = [
    path("webhook/", toggle_webhook, name="webhook"),
    path("enrich-video/<str:video_slug>/", enrich_video, name="enrich_video"),
    path(
        "enrich-subtitles/<str:video_slug>/",
        enrich_subtitles,
        name="enrich_subtitles"
    ),
    path(
        "enrich-video/<str:video_slug>/json/",
        enrich_video_json,
        name="enrich_video_json"
    ),
]
