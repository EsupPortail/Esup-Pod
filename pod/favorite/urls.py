from django.urls import path

from .views import favorite_button_in_video_info, favorite_list

app_name = "favorite"

urlpatterns = [
    path("", favorite_button_in_video_info, name="add-or-remove"),
    path("list/", favorite_list, name="list")
]
