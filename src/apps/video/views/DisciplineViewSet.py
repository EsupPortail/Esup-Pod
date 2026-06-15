"""
Esup-Pod - DisciplineViewSet.
"""

from rest_framework import viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view

from src.apps.video.models import Discipline
from src.apps.video.permissions import IsStaffOrReadOnly
from src.apps.video.serializers import DisciplineSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List all disciplines",
        description="Retrieve a list of all academic disciplines or subject fields available to categorize videos.",
    ),
    retrieve=extend_schema(
        summary="Retrieve a discipline",
        description="Retrieve details of a specific discipline by its ID.",
    ),
    create=extend_schema(
        summary="Create a discipline",
        description="Create a new academic discipline. Restricted to staff/administrator users.",
    ),
    update=extend_schema(
        summary="Update a discipline",
        description="Fully update an existing academic discipline. Restricted to staff/administrator users.",
    ),
    partial_update=extend_schema(
        summary="Partially update a discipline",
        description="Partially update an existing academic discipline. Restricted to staff/administrator users.",
    ),
    destroy=extend_schema(
        summary="Delete a discipline",
        description="Delete a discipline. Restricted to staff/administrator users.",
    ),
)
class DisciplineViewSet(viewsets.ModelViewSet):
    """
    API view set for the Discipline model.
    """

    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = [IsStaffOrReadOnly]
