"""
Esup-Pod - Tag viewset.
"""

from rest_framework import viewsets, filters
from src.apps.video.serializers import TagSerializer
from src.apps.video.models import Video


from src.apps.video.permissions import IsStaffOrReadOnly


class TagViewSet(viewsets.ModelViewSet):
    """
    Esup-Pod - API view set for Tags.
    """

    queryset = Video.tags.tag_model.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["count", "name"]
    ordering = ["-count", "name"]
