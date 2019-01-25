from django.conf.urls import url
from .views import lives
from .views import video_live, change_status

app_name = 'live'

urlpatterns = [
    url(r'^$',
        lives,
        name='lives'),
    url(r'^(?P<id>[\d]+)/$',
        video_live,
        name='video_live')
    url(r'^(?P<slug>[\-\d\w]+)/$',
        change_status,
        name='change_status')
]
