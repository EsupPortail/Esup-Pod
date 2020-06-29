from django.conf.urls import url

from . import views
app_name = "custom"

urlpatterns = [
    url(r'^$', views.index, name="home"),
    url(r'^update-owner/$', views.update_owner, name="update_video_owner"),
    url(r'^stats-videos/(?P<slug>[-\w]+)/$', views.stats_view, name="stats_videos"),
    url(
        r'^stats-videos/(?P<slug>[-\w]+)/(?P<slug_t>[-\w]+)/$',
        views.stats_view, name="stats_videos"),
]
