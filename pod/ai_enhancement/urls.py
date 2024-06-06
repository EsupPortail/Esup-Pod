"""URL patterns used in ai_enhancement application."""

from django.urls import path

from pod.ai_enhancement.views import (
    delete_enhance_video,
    enhance_subtitles,
    enhance_quiz,
    enhance_video,
    enhance_video_json,
    toggle_webhook,
)

app_name = "ai_enhancement"

urlpatterns = [
    path("webhook/", toggle_webhook, name="webhook"),
    path("delete/<slug:video_slug>/", delete_enhance_video, name="delete_enhance_video"),
    path("enhance_video/<slug:video_slug>/", enhance_video, name="enhance_video"),
    path(
        "enhance_subtitles/<slug:video_slug>/",
        enhance_subtitles,
        name="enhance_subtitles",
    ),
    path("enhance_quiz/<slug:video_slug>/", enhance_quiz, name="enhance_quiz"),
    path(
        "enhance_video_json/<slug:video_slug>/json/",
        enhance_video_json,
        name="enhance_video_json",
    ),
]
