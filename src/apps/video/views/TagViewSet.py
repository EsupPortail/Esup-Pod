"""
Esup-Pod - Tag viewset.
"""

from rest_framework import viewsets, permissions, filters
from src.apps.video.serializers import TagSerializer
from src.apps.video.models import Video


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Esup-Pod - API view set for Tags (auto-complete).
    """

    queryset = Video.tags.tag_model.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["count", "name"]
    ordering = ["-count", "name"]
