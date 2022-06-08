from django.urls import include, path
from .views import videos

app_name = "videos"

urlpatterns = [path("", videos, name="videos")]