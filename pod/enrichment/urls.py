from django.urls import re_path
from .views import edit_enrichment
from .views import video_enrichment
from .views import group_enrichment

app_name = "enrichment"

urlpatterns = [
    re_path(r"^edit/(?P<slug>[\-\d\w]+)/$", edit_enrichment, name="edit_enrichment"),
    re_path(
        r"^group/(?P<slug>[\-\d\w]+)/$",
        group_enrichment,
        name="group_enrichment",
    ),
    re_path(
        r"^video/(?P<slug>[\-\d\w]+)/$",
        video_enrichment,
        name="video_enrichment",
    ),
    re_path(
        r"^video/(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$",
        video_enrichment,
        name="video_enrichment_private",
    ),
]
