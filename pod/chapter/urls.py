from django.conf.urls import url
from pod.chapter.views import video_chapter

urlpatterns = [
    url(
        r"^video_chapter/(?P<slug>[\-\d\w]+)/$",
        video_chapter,
        name="video_chapter",
    ),
]
