from django.urls import path
from django.conf import settings

from .views import (
    channel_stats_view,
    general_stats_view,
    playlist_stats_view,
    to_do,
    user_stats_view,
    video_stats_view,
)

app_name = "stats"

if getattr(settings, "USE_STATS_VIEW", False):
    urlpatterns = [
        path("", general_stats_view, name="general-stats"),
        # USERS
        path("my-stats/", user_stats_view, name="my-stats"),
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
        path("playlists/", playlist_stats_view, name="playlist-stats"),
        path("playlists/<slug:playlist>", playlist_stats_view, name="playlist-stats"),
        # MEETINGS
        path("meetings/", to_do, name="meeting-stats"),
        path("meetings/<slug:meetings>", to_do, name="meeting-stats"),
    ]
