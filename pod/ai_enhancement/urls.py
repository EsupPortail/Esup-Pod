from django.urls import path

from pod.ai_enhancement.views import receive_webhook

app_name = "ai_enhancement"

urlpatterns = [
    path("webhook/", receive_webhook, name="webhook"),
]
