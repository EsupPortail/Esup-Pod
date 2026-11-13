"""
Esup-Pod - Role viewset.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from src.apps.authentication.permissions import IsSuperUser
from src.apps.completion.models import Role
from src.apps.completion.serializers import RoleSerializer


class RoleViewSet(viewsets.ModelViewSet):
    """
    API view set for Role management.
    Authenticated users can read roles. Superusers can manage them.
    """

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["code", "label"]
    filterset_fields = ["is_active"]
    ordering_fields = ["order", "label", "code"]
    ordering = ["order", "label"]

    def get_permissions(self):
        """Return permissions based on the action."""
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        # Modification, creation, deletion restricted to superusers
        return [IsSuperUser()]
