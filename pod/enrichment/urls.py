from django.conf.urls import url
from .views import edit_enrichment
from .views import video_enrichment

app_name = 'enrichment'

urlpatterns = [
    url(r'^edit/(?P<slug>[\-\d\w]+)/$',
        edit_enrichment,
        name='edit_enrichment'),
    url(r'^video/(?P<slug>[\-\d\w]+)/$',
        video_enrichment,
        name='video_enrichment')
]
