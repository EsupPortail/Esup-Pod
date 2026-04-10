"""
Esup-Pod - DisciplineViewSet.
"""

from rest_framework import viewsets, permissions
from src.apps.video.models import Discipline
from src.apps.video.serializers import DisciplineSerializer


class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Esup-Pod - API view set for the Discipline model (Read-only).
    """

    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = [permissions.AllowAny]
