from django.urls import path
from django.conf import settings

from .views import (
    channel_stats_view,
    to_do,
    video_stats_view,
)

app_name = "stats"

if getattr(settings, "USE_STATS_VIEW", False):
    urlpatterns = [
        path("", to_do, name="general-stats"),
        # USERS
        path("my-stats/", to_do, name="my-stats"),
        # VIDEOS
        path("videos/", video_stats_view, name="video-stats"),
        path("videos/<slug:video>", video_stats_view, name="video-stats"),
        # CHANNELS
        path("channels/", channel_stats_view, name="channels-stats"),
        path("channels/<slug:channel>", channel_stats_view, name="channels-stats"),
        path(
            "channels/<slug:channel>/<slug:theme>",
            channel_stats_view,
            name="channels-stats",
        ),
        # PLAYLISTS
        path("playlists/", to_do, name="playlist-stats"),
        path("playlists/<slug:playlist>", to_do, name="playlist-stats"),
        # MEETINGS
        path("meetings/", to_do, name="meeting-stats"),
        path("meetings/<slug:meetings>", to_do, name="meeting-stats"),
    ]
