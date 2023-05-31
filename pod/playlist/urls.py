from django.urls import path

from .views import playlist_content, playlist_list

app_name = "playlist"

urlpatterns = [
    path("", playlist_list, name="list"),
    path("<slug:slug>", playlist_content, name="content"),
]
