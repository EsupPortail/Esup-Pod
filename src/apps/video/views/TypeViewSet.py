"""
Esup-Pod - TypeViewSet.
"""

from rest_framework import viewsets
from src.apps.video.models import Type
from src.apps.video.serializers import TypeSerializer


from src.apps.video.permissions import IsStaffOrReadOnly


class TypeViewSet(viewsets.ModelViewSet):
    """
    Esup-Pod - API view set for the Type model.
    """

    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = [IsStaffOrReadOnly]
