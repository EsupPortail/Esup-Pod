from django.conf.urls import url
from pod.enrichment.views import video_enrichment

urlpatterns = [
    url(r'^video_enrichment/(?P<slug>[\-\d\w]+)/$',
        video_enrichment,
        name='video_enrichment'),
]
