from django.conf.urls import url

from . import views

app_name = "custom"

urlpatterns = [
    url(r'^$', views.index, name="home"),
    url(r'^manage/videos/put/(?P<user_id>[\d]+)/$',
        views.update_video_owner,
        name="update_video_owner"
    ),
    url(r'^manage/videos/owners/$',
        views.get_owners,
        name="get_owners"
    ),
    url(r'^manage/videos/(?P<user_id>[\d]+)/$',
        views.get_videos,
        name="get_videos"
    ),
]
