"""
Esup-Pod - API router configuration.
"""

from rest_framework import routers
from src.apps.video.views import VideoViewSet, SubtitleViewSet

router = routers.SimpleRouter()
router.register(r"videos", VideoViewSet, basename="video")
router.register(r"subtitles", SubtitleViewSet, basename="subtitle")
