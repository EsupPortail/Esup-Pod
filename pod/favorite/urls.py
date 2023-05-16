from django.urls import path

from .views import favorite_button_in_video_info, favorite_list
from .views import favorites_save_reorganisation

app_name = "favorite"

urlpatterns = [
    path("", favorite_button_in_video_info, name="add-or-remove"),
    path("list/", favorite_list, name="list"),
    path(
        "save-reorganisation/",
        favorites_save_reorganisation,
        name="save-reorganisation"
    ),
]
