from django.urls import path
from .views import channel_edit
from .views import theme_edit
from .views import my_channels

app_name = "channels"

urlpatterns = [
    path("my/", my_channels, name="my_channels"),
    path(
        "edit/<slug:slug>/",
        channel_edit,
        name="channel_edit",
    ),
    path("theme/edit/<slug:slug>/", theme_edit, name="theme_edit"),
]
