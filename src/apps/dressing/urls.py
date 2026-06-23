"""
Esup-Pod - Dressing URL patterns.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DressingViewSet, CustomImageViewSet

router = DefaultRouter()
router.register(r"dressing", DressingViewSet, basename="dressing")
router.register(r"watermarks", CustomImageViewSet, basename="watermarks")

urlpatterns = [
    path("", include(router.urls)),
]
