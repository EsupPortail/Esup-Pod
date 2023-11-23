from django.conf.urls import url
from pod.dressing.views import video_dressing, my_dressings, dressing_edit
from pod.dressing.views import dressing_create, dressing_delete

app_name = "dressing"

urlpatterns = [
    url(r"^my/$", my_dressings, name="my_dressings"),
    url(r"^edit/(?P<dressing_id>[\-\d\w]+)/$", dressing_edit, name="dressing_edit"),
    url(r"^new/$", dressing_create, name="dressing_create"),
    url(r"^delete/(?P<dressing_id>[\-\d\w]+)/$", dressing_delete, name="dressing_delete"),
    url(r"^(?P<slug>[\-\d\w]+)/$", video_dressing, name="video_dressing"),
]
