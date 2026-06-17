"""
Esup-Pod - Completion permissions.
"""

from rest_framework import permissions


class IsVideoOwnerOrCoOwnerOrHasPerm(permissions.BasePermission):
    """
    Reproduces V4 has_video_rights logic:
    Access allowed if user is:
      - video owner OR
      - co-owner (collaborators/additional_owners) OR
      - superuser OR
      - has the specified Django permission
    """

    perm_codename = None

    def has_object_permission(self, request, view, obj):
        """Check if user has permission for the object."""
        video = obj if hasattr(obj, "owner") else obj.video
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return (
            user == video.owner
            or user.is_superuser
            or user in video.co_owners.all()
            or (self.perm_codename and user.has_perm(self.perm_codename))
        )


class CanManageContribution(IsVideoOwnerOrCoOwnerOrHasPerm):
    """Contribution: owner/co-owner + staff/superuser or has perm."""

    perm_codename = "completion.add_contribution_anywhere"


class CanManageDocument(IsVideoOwnerOrCoOwnerOrHasPerm):
    """Document: owner/co-owner + staff/superuser or has perm."""

    perm_codename = "completion.add_document_anywhere"


class CanManageOverlay(IsVideoOwnerOrCoOwnerOrHasPerm):
    """Overlay: owner/co-owner + staff/superuser or has perm."""

    perm_codename = "completion.add_overlay_anywhere"
