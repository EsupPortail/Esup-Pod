"""
Esup-Pod - Dressing views.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from src.apps.dressing.models import Dressing
from src.apps.dressing.serializers import DressingSerializer, CustomImageSerializer
from src.apps.dressing.permissions import IsDressingEnabled, CanManageDressing
from src.apps.utils.models import CustomImageModel


class CustomImageViewSet(viewsets.ModelViewSet):
    """
    API endpoints for watermark images (CustomImageModel).
    """

    serializer_class = CustomImageSerializer
    permission_classes = [IsAuthenticated, IsDressingEnabled]

    def get_queryset(self):
        """Filter watermark images so users only see their own uploads (except superusers)."""
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return CustomImageModel.objects.all()
        return CustomImageModel.objects.filter(created_by=user)

    def perform_create(self, serializer):
        """Save the custom image and set the creator as owner."""
        serializer.save(created_by=self.request.user)


class DressingViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Video Dressings.
    Users can see dressings they own, are users of, or that are allowed to their groups.
    """

    serializer_class = DressingSerializer
    permission_classes = [IsAuthenticated, IsDressingEnabled, CanManageDressing]

    def get_queryset(self):
        """Retrieve dressing configurations matching the user's rights (owner, user, or group)."""
        user = self.request.user
        if getattr(user, "is_superuser", False):
            return Dressing.objects.all()

        # Check groups
        # Assuming user has an owner profile with access_groups
        groups = []
        if hasattr(user, "owner") and getattr(user.owner, "access_groups", None):
            groups = user.owner.access_groups.all()

        q_filter = Q(owners=user) | Q(users=user) | Q(allow_to_groups__in=groups)
        return Dressing.objects.filter(q_filter).distinct()

    def perform_create(self, serializer):
        """Save the dressing instance and associate the creator as an owner."""
        # The user creating the dressing becomes an owner by default
        instance = serializer.save()
        instance.owners.add(self.request.user)
