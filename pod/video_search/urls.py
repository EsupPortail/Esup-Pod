from django.conf.urls import url

from .views import search_videos

app_name = "video_search"

urlpatterns = [url(r"^$", search_videos, name="search_videos")]
