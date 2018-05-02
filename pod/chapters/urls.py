from django.conf.urls import url
from pod.chapters.views import video_chapter
from pod.chapters.views import get_chapter_vtt

urlpatterns = [
    url(r'^video_chapter/(?P<slug>[\-\d\w]+)/$',
        video_chapter,
        name='video_chapter'),
    url(r'^get_chapter_vtt/(?P<slug>[\-\d\w]+)/$',
        get_chapter_vtt,
        name='get_chapter_vtt'),
]
