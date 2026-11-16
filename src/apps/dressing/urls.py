"""
Esup-Pod - Dressing URL patterns.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomImageViewSet, DressingViewSet

router = DefaultRouter()
router.register(r"dressing", DressingViewSet, basename="dressing")
router.register(r"watermarks", CustomImageViewSet, basename="watermarks")

urlpatterns = [
    path("", include(router.urls)),
]
