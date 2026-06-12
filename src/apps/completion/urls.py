"""
Esup-Pod - Completion URLs.
"""

from rest_framework.routers import SimpleRouter
from src.apps.completion.views import (
    ContributorViewSet,
    ContributionViewSet,
    DocumentViewSet,
    OverlayViewSet,
)

router = SimpleRouter()
router.register(r"contributors", ContributorViewSet, basename="contributor")
router.register(r"contributions", ContributionViewSet, basename="contribution")
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"overlays", OverlayViewSet, basename="overlay")

urlpatterns = router.urls
