"""
Esup-Pod - DisciplineViewSet.
"""

from rest_framework import viewsets
from src.apps.video.models import Discipline
from src.apps.video.serializers import DisciplineSerializer


from src.apps.video.permissions import IsStaffOrReadOnly


class DisciplineViewSet(viewsets.ModelViewSet):
    """
    Esup-Pod - API view set for the Discipline model.
    """

    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = [IsStaffOrReadOnly]
