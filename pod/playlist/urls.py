from django.urls import path

from .views import add_video_in_playlist, playlist_content, playlist_list
from .views import remove_playlist_view, remove_video_in_playlist

app_name = "playlist"

urlpatterns = [
    path("", playlist_list, name="list"),
    path("<slug:slug>/", playlist_content, name="content"),
    path("remove/<slug:slug>/", remove_playlist_view, name="remove"),
    path(
        "remove/<slug:slug>/<slug:video_slug>/",
        remove_video_in_playlist,
        name="remove-video"
    ),
    path("add/<slug:slug>/<slug:video_slug>/", add_video_in_playlist, name="add-video"),
]
