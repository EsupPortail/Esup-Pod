from django.urls import path
from .views import videos

app_name = "videos"

urlpatterns = [path("", videos, name="videos")]
