"""
Esup-Pod - Overlay viewset.
"""

from rest_framework import viewsets, permissions, filters
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend

from src.apps.completion.models import Overlay
from src.apps.completion.serializers import OverlaySerializer
from src.apps.completion.permissions import CanManageOverlay


class OverlayViewSet(viewsets.ModelViewSet):
    """
    API view set for the Overlay model.
    """

    queryset = Overlay.objects.all().select_related("video")
    serializer_class = OverlaySerializer
    permission_classes = [permissions.IsAuthenticated, CanManageOverlay]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["video"]
    ordering_fields = ["time_start", "id"]
    ordering_fields = ["time_start", "id"]
    ordering = ["time_start"]

    def perform_create(self, serializer):
        """Handle overlay creation with permission checks."""
        video = serializer.validated_data.get("video")
        user = self.request.user
        if video and not (
            user == video.owner
            or user.is_superuser
            or user in video.co_owners.all()
            or user.has_perm("completion.add_overlay_anywhere")
        ):
            raise PermissionDenied(
                _("You do not have permission to add an overlay to this video.")
            )
        serializer.save()
