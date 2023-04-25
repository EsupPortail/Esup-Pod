from django.urls import path

from .views import favorite_button_in_video_info

app_name = "favorite"

urlpatterns = [
    path("", favorite_button_in_video_info, name="add-or-remove"),
]
