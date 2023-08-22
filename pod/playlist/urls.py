from django.urls import path

from .views import (
    add_or_edit,
    add_video_in_playlist,
    get_video,
    playlist_content,
    playlist_list,
    remove_playlist_view,
    remove_video_in_playlist,
    favorites_save_reorganisation,
    start_playlist,
)

app_name = "playlist"

urlpatterns = [
    path("", playlist_list, name="list"),
    path("add/", add_or_edit, name="add"),
    path("edit/<slug:slug>/", add_or_edit, name="edit"),
    path("remove/<slug:slug>/", remove_playlist_view, name="remove"),
    path(
        "remove/<slug:slug>/<slug:video_slug>/",
        remove_video_in_playlist,
        name="remove-video"
    ),
    path(
        "add/<slug:slug>/<slug:video_slug>/",
        add_video_in_playlist,
        name="add-video",
    ),
    path("get-video/<slug:video_slug>/<slug:playlist_slug>/", get_video, name="get-video"),
    path("<slug:slug>/", playlist_content, name="content"),
    path(
        "<slug:slug>/save-reorganisation/",
        favorites_save_reorganisation,
        name="save-reorganisation"
    ),
    path("start-playlist/<slug:slug>", start_playlist, name="start-playlist"),
    path(
        "start-playlist/<slug:slug>/<slug:video>",
        start_playlist,
        name="start-playlist"
    ),
]
