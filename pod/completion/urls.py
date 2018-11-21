from django.conf.urls import url
from .views import video_completion
from .views import video_caption_maker
from .views import video_completion_contributor
from .views import video_completion_document
from .views import video_completion_track
from .views import video_completion_overlay

urlpatterns = [
    url(r'^video_completion/(?P<slug>[\-\d\w]+)/$',
        video_completion,
        name='video_completion'),
    url(r'^video_caption_maker/(?P<slug>[\-\d\w]+)/$',
        video_caption_maker,
        name='video_caption_maker'),
    url(r'^video_completion_contributor/(?P<slug>[\-\d\w]+)/$',
        video_completion_contributor,
        name='video_completion_contributor'),
    url(r'^video_completion_document/(?P<slug>[\-\d\w]+)/$',
        video_completion_document,
        name='video_completion_document'),
    url(r'^video_completion_track/(?P<slug>[\-\d\w]+)/$',
        video_completion_track,
        name='video_completion_track'),
    url(r'^video_completion_overlay/(?P<slug>[\-\d\w]+)/$',
        video_completion_overlay,
        name='video_completion_overlay'),
]
