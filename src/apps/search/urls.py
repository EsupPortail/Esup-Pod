"""
Esup-Pod - Search application URL configuration.
"""

from rest_framework.routers import SimpleRouter

from src.apps.search.views import SearchViewSet

router = SimpleRouter()
router.register(r"search", SearchViewSet, basename="search")

urlpatterns = router.urls
