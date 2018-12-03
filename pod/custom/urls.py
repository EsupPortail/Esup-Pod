from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.VideoListView.as_view(), name="home_pod"),
]
