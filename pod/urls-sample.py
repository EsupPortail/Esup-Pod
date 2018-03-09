"""
pod_project URL Configuration
"""

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL,
			      document_root=settings.MEDIA_ROOT)
