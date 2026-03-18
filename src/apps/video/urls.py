from rest_framework.routers import SimpleRouter
from src.apps.video.views import VideoViewSet, SubtitleViewSet

router = SimpleRouter()
router.register(r"videos", VideoViewSet, basename="video")
router.register(r"subtitles", SubtitleViewSet, basename="subtitle")

urlpatterns = router.urls
