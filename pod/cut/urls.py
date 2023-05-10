from django.conf.urls import url
from pod.cut.views import cut_video

app_name = "cut"

urlpatterns = [
    url(r"^(?P<slug>[\-\d\w]+)/$", cut_video, name="video_cut"),
]
