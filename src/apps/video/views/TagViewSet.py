"""
Esup-Pod - Tag viewset.
"""

from rest_framework import filters, viewsets

from src.apps.video.models import Video
from src.apps.video.permissions import IsStaffOrReadOnly
from src.apps.video.serializers import TagSerializer


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
