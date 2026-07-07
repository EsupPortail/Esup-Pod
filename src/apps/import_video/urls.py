"""
Esup-Pod - Import Video application URL configuration.
"""

from rest_framework.routers import SimpleRouter
from src.apps.import_video.views import ExternalRecordingViewSet
from src.apps.import_video.conf import import_video_settings

router = SimpleRouter()

if import_video_settings.use_import_video:
    router.register(
        r"external-recordings",
        ExternalRecordingViewSet,
        basename="external-recording",
    )

urlpatterns = router.urls
