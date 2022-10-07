from django.urls import path
from .views import channel
from .views import video

app_name = "channel-video"

urlpatterns = [
    path("<slug:slug_c>/", channel, name="channel"),
    path("<slug:slug_c>/<slug:slug_t>/", channel, name="theme"),
    path(
        "<slug:slug_c>/video/<slug:slug>/",
        video,
        name="video",
    ),
    path(
        "<slug:slug_c>/<slug:slug_t>/video/<slug:slug>/",
        video,
        name="video",
    ),
]
