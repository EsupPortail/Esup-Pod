"""
pod_project URL Configuration
"""

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.apps import apps
from pod.video.views import video
from pod.video.views import video_edit
from pod.video.views import channel
from pod.video.views import videos

if apps.is_installed('pod.filepicker'):
    from pod.filepicker.sites import site as filepicker_site

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Translation
    url(r'^i18n/', include('django.conf.urls.i18n')),

    # App video
    url(r'^videos/$', videos, name='videos'),
    url(r'^video/(?P<slug>[\-\d\w]+)/$', video, name='video'),
    url(r'^video_edit/$', video_edit, name='video_edit'),
    url(r'^video_edit/(?P<slug>[\-\d\w]+)/$', video_edit, name='video_edit'),
]

if apps.is_installed('pod.filepicker'):
    urlpatterns += [url(r'^file-picker/', include(filepicker_site.urls)), ]
if apps.is_installed('pod.completion'):
    urlpatterns += [url(r'^', include('pod.completion.urls')), ]
if apps.is_installed('pod.chapters'):
    urlpatterns += [url(r'^', include('pod.chapters.urls')), ]
if apps.is_installed('pod.enrichment'):
    urlpatterns += [url(r'^', include('pod.enrichment.urls')), ]


urlpatterns += [
    url(r'^(?P<slug_c>[\-\d\w]+)/$', channel, name='channel'),
    # url(r'^(?P<slug_c>[\-\d\w]+)/edit$',
    #    'pods.views.channel_edit', name='channel_edit'),
    url(r'^(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$',
        channel, name='theme'),
    url(r'^(?P<slug_c>[\-\d\w]+)/video/(?P<slug>[\-\d\w]+)/$',
        video, name='video'),
    url(r'^(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/video/(?P<slug>[\-\d\w]+)/$',
        video, name='video'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
