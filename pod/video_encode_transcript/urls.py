"""URL patterns used for Esup-Pod in video_encode_transcript application."""

from django.urls import path
from pod.video_encode_transcript.views import notify_task_end

app_name = "video_encode_transcript"

urlpatterns = [
    # This endpoint is called by the runner manager when a task is completed, to update the task status and send notifications.
    path("notify_task_end/", notify_task_end, name="notify_task_end"),
]
