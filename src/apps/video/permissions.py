"""
Esup-Pod - Video permissions.
"""

from rest_framework import permissions
from .conf import video_settings


class IsOwnerOrCoOwnerOrChannelCollaborator(permissions.BasePermission):
    """
    Esup-Pod - Custom permission:
    - Read (GET, HEAD, OPTIONS) allowed for everyone (depending on the view).
    - Write (PUT, PATCH, DELETE) allowed only for the owner, co-owners,
      or collaborators of the video's channel.
    """

    def has_object_permission(self, request, view, obj):
        """Object-level permission check for ownership, collaboration, or staff status."""
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        # 1. Superusers have all rights
        if request.user.is_superuser:
            return True

        # 2. Video Owner can always edit their content
        if obj.owner == request.user:
            return True

        # 3. Restrict editing to staff only: non-staff users cannot edit (as co-owners/collaborators)
        if video_settings.restrict_edit_to_staff and not request.user.is_staff:
            return False

        # 4. Video Co-owner
        if obj.co_owners.filter(pk=request.user.pk).exists():
            return True

        # 5. Channel Owner/Collaborator
        if obj.channel:
            is_channel_owner = obj.channel.owner == request.user
            is_channel_collab = obj.channel.collaborators.filter(
                pk=request.user.pk
            ).exists()
            return is_channel_owner or is_channel_collab

        return False


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Esup-Pod - Custom permission:
    - Read (GET, HEAD, OPTIONS) allowed for everyone.
    - Write (POST, PUT, PATCH, DELETE) allowed only for staff/superusers.
    """

    def has_permission(self, request, view):
        """Check if the user is staff for non-safe methods."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and (request.user.is_staff or request.user.is_superuser))
