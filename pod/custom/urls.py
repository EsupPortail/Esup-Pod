from django.conf.urls import url
from . import views

urlpatterns = [
    urls(r'^$', views.VideoListView.as_view(), name="home_pod"),
]
