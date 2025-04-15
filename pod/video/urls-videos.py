from django.urls import path
from .views import videos , dashboard

app_name = "videos"

urlpatterns = [path("", videos, name="videos"),
               path('dashboard/', dashboard, name='dashboard'),
               ]
