"""
pod_project URL Configuration
"""

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from pod.filepicker.sites import site as filepicker_site


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Exterior apps
    url(r'^file-picker/', include(filepicker_site.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
