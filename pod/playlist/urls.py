from django.urls import path

from .views import playlist_list

app_name = "playlist"

urlpatterns = [
    path("", playlist_list, name="list"),
]
