from django.conf.urls import url

from . import views

app_name = "custom"

urlpatterns = [
    url(r'^$', views.update_owner, name="home"),
    url(r'^update-owner/$', views.index, name="update_video_owner"),
]
