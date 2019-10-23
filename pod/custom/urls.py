from django.conf.urls import url

from . import views
app_name = "custom"

urlpatterns = [
    url(r'^$', views.index, name="home"),
    url(r'^update-owner/$', views.update_owner, name="update_video_owner"),
]
