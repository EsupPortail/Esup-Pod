"""
Esup-Pod - Live URL configuration.
"""

from rest_framework.routers import DefaultRouter
from src.apps.live.views import BuildingViewSet, BroadcasterViewSet, EventViewSet

router = DefaultRouter()
router.register(r"live/buildings", BuildingViewSet, basename="building")
router.register(r"live/broadcasters", BroadcasterViewSet, basename="broadcaster")
router.register(r"live/events", EventViewSet, basename="event")

urlpatterns = router.urls
