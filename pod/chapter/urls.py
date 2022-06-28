from django.conf.urls import url
from pod.chapter.views import video_chapter

app_name = "chapter"

urlpatterns = [
    url(
        r"^(?P<slug>[\-\d\w]+)/$",
        video_chapter,
        name="video_chapter",
    ),
]
