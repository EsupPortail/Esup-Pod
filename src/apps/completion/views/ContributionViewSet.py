"""
Esup-Pod - Contribution viewset.
"""

from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend

from src.apps.completion.models import Contribution
from src.apps.completion.serializers import ContributionSerializer
from src.apps.completion.permissions import CanManageContribution


class ContributionViewSet(viewsets.ModelViewSet):
    """
    API view set for the Contribution model.
    """

    queryset = Contribution.objects.all().select_related("video", "contributor")
    serializer_class = ContributionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageContribution]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["video", "role", "contributor"]
    ordering_fields = ["id"]
    ordering_fields = ["id"]
    ordering = ["id"]

    def perform_create(self, serializer):
        """Handle contribution creation with permission checks."""
        video = serializer.validated_data.get("video")
        user = self.request.user
        if video and not (
            user == video.owner
            or user.is_superuser
            or user.is_staff
            or user in video.co_owners.all()
            or user.has_perm("completion.add_contribution")
        ):
            raise PermissionDenied(
                "You do not have permission to add a contribution to this video."
            )
        serializer.save()

    def get_queryset(self):
        """
        Optionally filter by video if 'video' is passed.
        Also we might prefetch objects needed for permissions.
        """
        qs = super().get_queryset()
        return qs
