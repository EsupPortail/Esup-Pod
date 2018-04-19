"""
pod_project URL Configuration
"""

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.apps import apps


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Exterior apps
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

if apps.is_installed('pod.filepicker'):
    from pod.filepicker.sites import site as filepicker_site
    urlpatterns += [url(r'^file-picker/', include(filepicker_site.urls)), ]
if apps.is_installed('pod.chapters'):
    from pod.chapters.views import video_chapter
    from pod.chapters.views import get_chapter_vtt
    urlpatterns += [
        url(r'^video_chapter/(?P<slug>[\-\d\w]+)/$',
        video_chapter, 
        name='video_chapter'), 
        url(r'^get_chapter_vtt/(?P<slug>[\-\d\w]+)/$',
        get_chapter_vtt,
        name='get_chapter_vtt'),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
