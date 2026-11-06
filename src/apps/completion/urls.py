"""
Esup-Pod - Completion URLs.
"""

from rest_framework.routers import SimpleRouter
from src.apps.completion.views import (
    ContributorViewSet,
    ContributionViewSet,
    DocumentViewSet,
    OverlayViewSet,
    RoleViewSet,
)

router = SimpleRouter()
router.register(r"contributors", ContributorViewSet, basename="contributor")
router.register(r"contributions", ContributionViewSet, basename="contribution")
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"overlays", OverlayViewSet, basename="overlay")
router.register(r"roles", RoleViewSet, basename="role")

urlpatterns = router.urls
