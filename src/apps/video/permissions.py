"""
Esup-Pod - Video permissions.
"""

from rest_framework import permissions
from .conf import video_settings


class IsOwnerOrCoOwnerOrReadOnly(permissions.BasePermission):
    """
    Esup-Pod - Custom permission:
    - Read (GET, HEAD, OPTIONS) allowed for everyone (depending on the view).
    - Write (PUT, PATCH, DELETE) allowed only for the owner.
    """

    def has_object_permission(self, request, view, obj):
        """Object-level permission check for ownership or staff status."""
        if request.method in permissions.SAFE_METHODS:
            return True
        if video_settings.restrict_edit_to_staff:
            return request.user and (request.user.is_staff or request.user.is_superuser)
        is_owner = obj.owner == request.user
        is_staff = request.user.is_staff or request.user.is_superuser
        is_co_owner = request.user in obj.co_owners.all()
        if request.method == "DELETE":
            return is_owner or is_staff
        return is_owner or is_co_owner or is_staff


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
