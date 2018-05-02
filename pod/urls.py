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
]

if apps.is_installed('pod.filepicker'):
    urlpatterns += [url(r'^file-picker/', include(filepicker_site.urls)), ]
if apps.is_installed('pod.completion'):
    urlpatterns += [url(r'^', include('pod.completion.urls')), ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
