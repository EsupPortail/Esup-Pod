from django.conf.urls import url
from .views import lives
from .views import video_live

app_name = 'live'

urlpatterns = [
    url(r'^$',
        lives,
        name='lives'),
    url(r'^(?P<slug>[\-\d\w]+)/$', video_live, name='video_live'),
]
