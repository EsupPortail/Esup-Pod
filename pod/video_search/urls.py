from django.urls import re_path

from .views import search_videos

app_name = "video_search"

urlpatterns = [re_path(r"^$", search_videos, name="search_videos")]
