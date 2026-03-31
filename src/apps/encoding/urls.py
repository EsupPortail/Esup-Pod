"""
Esup-Pod - Encoding app URL configuration.
"""

from django.urls import path
from .views.webhook import EncodingWebhookView

app_name = "encoding"

urlpatterns = [
    path("webhook/", EncodingWebhookView.as_view(), name="webhook"),
]
