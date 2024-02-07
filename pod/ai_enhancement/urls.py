from django.urls import path

from pod.ai_enhancement.views import enrich_video, receive_webhook

app_name = "ai_enhancement"

urlpatterns = [
    path("webhook/", receive_webhook, name="webhook"),
    path("enrich_video/<str:video_slug>/", enrich_video, name="enrich_video"),
]
