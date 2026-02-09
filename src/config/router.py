from rest_framework import routers
from src.apps.video.views import VideoViewSet

router = routers.SimpleRouter()
router.register(r'videos', VideoViewSet, basename='video')
