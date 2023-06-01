from django.urls import path

from .views import playlist_content, playlist_list, remove_video_in_playlist

app_name = "playlist"

urlpatterns = [
    path("remove-video", remove_video_in_playlist, name="remove-video"),
    path("", playlist_list, name="list"),
    path("<slug:slug>", playlist_content, name="content"),
]
