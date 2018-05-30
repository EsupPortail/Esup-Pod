from django.conf.urls import url
from pod.enrichment.views import video_enrichment
from pod.enrichment.views import video_enriched

urlpatterns = [
    url(r'^video_enrichment/(?P<slug>[\-\d\w]+)/$',
        video_enrichment,
        name='video_enrichment'),
   	url(r'^video_enriched/(?P<slug>[\-\d\w]+)/$',
   		video_enriched,
   		name='video_enriched'),
]
