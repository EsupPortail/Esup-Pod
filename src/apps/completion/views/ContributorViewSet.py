"""
Esup-Pod - Contributor viewset.
"""

from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from src.apps.completion.models import Contributor
from src.apps.completion.serializers import ContributorSerializer
from src.apps.authentication.permissions import IsSuperUser


class ContributorViewSet(viewsets.ModelViewSet):
    """
    API view set for the global Contributor directory.
    Superusers can manage it. Everyone authenticated can read and search it.
    """

    queryset = Contributor.objects.all()
    serializer_class = ContributorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["first_name", "last_name", "email_address"]
    filterset_fields = ["first_name", "last_name", "email_address"]
    ordering_fields = ["last_name", "first_name", "created_at"]
    ordering = ["last_name", "first_name"]

    def get_permissions(self):
        """Return permissions based on the action."""
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated()]
        # Creation, Update, Deletion is restricted to superusers/admins
        return [IsSuperUser()]
