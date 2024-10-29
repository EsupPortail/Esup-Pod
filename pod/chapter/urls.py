from django.urls import re_path
from pod.chapter.views import video_chapter

app_name = "chapter"

urlpatterns = [
    re_path(
        r"^(?P<slug>[\-\d\w]+)/$",
        video_chapter,
        name="video_chapter",
    ),
]
