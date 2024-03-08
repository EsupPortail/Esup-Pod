"""URL patterns used in ai_enhancement application."""
from django.urls import path

from pod.ai_enhancement.views import (
    enhance_subtitles,
    enhance_video,
    enhance_video_json,
    toggle_webhook,
)

app_name = "ai_enhancement"

urlpatterns = [
    path("webhook/", toggle_webhook, name="webhook"),
    path("enrich-video/<str:video_slug>/", enhance_video, name="enhance_video"),
    path(
        "enrich-subtitles/<str:video_slug>/",
        enhance_subtitles,
        name="enhance_subtitles"
    ),
    path(
        "enrich-video/<str:video_slug>/json/",
        enhance_video_json,
        name="enhance_video_json"
    ),
]
