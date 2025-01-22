from django.urls import path
from .views import video_duplicate

app_name = "duplicate"

urlpatterns = [
    path("video_duplicate/<slug:slug>/", video_duplicate, name="video_duplicate"),
]
