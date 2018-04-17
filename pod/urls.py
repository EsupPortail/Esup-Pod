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


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    # App video
    url(r'^video/(?P<slug>[\-\d\w]+)/$', video, name='video')
]

if apps.is_installed('filepicker'):
    urlpatterns += [url(r'^file-picker/', include('pod.filepicker.urls')), ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
