"""
Esup-Pod - TypeViewSet.
"""

from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from src.apps.video.models import Type
from src.apps.video.permissions import IsStaffOrReadOnly
from src.apps.video.serializers import TypeSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all video types",
        description="Retrieve a list of all video categories or types configured in the application (e.g., Course, Conference, Interview).",
    ),
    retrieve=extend_schema(
        summary="Retrieve a video type",
        description="Retrieve detailed information about a specific video type by its ID.",
    ),
    create=extend_schema(
        summary="Create a video type",
        description="Add a new video type. Restricted to staff/administrator users.",
    ),
    update=extend_schema(
        summary="Update a video type",
        description="Fully update an existing video type. Restricted to staff/administrator users.",
    ),
    partial_update=extend_schema(
        summary="Partially update a video type",
        description="Partially update an existing video type. Restricted to staff/administrator users.",
    ),
    destroy=extend_schema(
        summary="Delete a video type",
        description="Delete a video type and remove it from the system. Restricted to staff/administrator users.",
    ),
)
class TypeViewSet(viewsets.ModelViewSet):
    """
    API view set for the Type model.
    """

    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [IsStaffOrReadOnly]
