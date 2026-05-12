"""
Esup-Pod - URL configuration for the collection app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from src.apps.collection.views import (
    ChannelViewSet,
    ThemeViewSet,
    PlaylistViewSet,
    FavoriteViewSet,
)

router = DefaultRouter()
router.register(r"channels", ChannelViewSet, basename="channel")
router.register(r"themes", ThemeViewSet, basename="theme")
router.register(r"playlists", PlaylistViewSet, basename="playlist")
router.register(r"favorites", FavoriteViewSet, basename="favorite")

urlpatterns = [
    path("", include(router.urls)),
]
