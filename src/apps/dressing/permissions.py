"""
Esup-Pod - Dressing permissions.
"""

from rest_framework import permissions
from src.apps.dressing.conf import dressing_settings


class IsDressingEnabled(permissions.BasePermission):
    """
    Permission check to ensure the dressing feature is enabled globally.
    """

    def has_permission(self, request, view):
        """Allow access only if the dressing feature is enabled."""
        return bool(dressing_settings.use_dressing)


class CanManageDressing(permissions.BasePermission):
    """
    Permission check to control dressing management based on settings.
    - Superusers / staff can always manage dressings.
    - If allow_user_custom_dressing is True, authenticated users can manage their own dressings.
    - If allow_user_custom_dressing is False, standard users can only read dressings, not create/modify them.
    """

    def has_permission(self, request, view):
        """Check action-level permissions."""
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True

        return bool(dressing_settings.allow_user_custom_dressing)

    def has_object_permission(self, request, view, obj):
        """Check object-level ownership / editing permissions."""
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return True

        # Check if the user is an owner of this dressing
        return obj.owners.filter(pk=user.pk).exists()
