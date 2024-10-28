"""Esup-Pod video search urls."""

from django.urls import path
from .views import search_videos

app_name = "video_search"

urlpatterns = [path("", search_videos, name="search_videos")]
