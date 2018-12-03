from django.conf.urls import urls
from . import views

urlpatterns = [
    urls(r'^$', views.VideoListView.as_view(), name="home_pod"),
]
