from django.urls import path
from .views import get_owners_for_videos_on_dashboard, videos , dashboard

app_name = "videos"

urlpatterns = [
    path("", videos, name="videos"),
    path('dashboard/', dashboard, name='dashboard'),
    path("dashboard/get_owners_for_videos_on_dashboard/", get_owners_for_videos_on_dashboard, name='dashboard-owners'),
]
