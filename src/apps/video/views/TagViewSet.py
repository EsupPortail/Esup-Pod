"""
Esup-Pod - Tag viewset.
"""

from rest_framework import filters, viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from src.apps.video.models import Video
from src.apps.video.permissions import IsStaffOrReadOnly
from src.apps.video.serializers import TagSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all tags",
        description="Retrieve a list of all tags used across videos. Features search and ordering capabilities based on tag usage count or name.",
    ),
    retrieve=extend_schema(
        summary="Retrieve a tag",
        description="Retrieve details of a specific tag by its ID.",
    ),
    create=extend_schema(
        summary="Create a tag",
        description="Create a new tag. Restricted to staff/administrator users.",
    ),
    update=extend_schema(
        summary="Update a tag",
        description="Fully update an existing tag. Restricted to staff/administrator users.",
    ),
    partial_update=extend_schema(
        summary="Partially update a tag",
        description="Partially update an existing tag. Restricted to staff/administrator users.",
    ),
    destroy=extend_schema(
        summary="Delete a tag",
        description="Delete a tag. Restricted to staff/administrator users.",
    ),
)
class TagViewSet(viewsets.ModelViewSet):
    """
    API view set for Tags.
    """

    queryset = Video.tags.tag_model.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["count", "name"]
    ordering = ["-count", "name"]
