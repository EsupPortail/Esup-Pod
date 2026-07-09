"""
Esup-Pod - Notes permissions.
"""

from rest_framework import permissions


class IsNoteOwner(permissions.BasePermission):
    """
    Allows read access to authenticated users.
    Restricts write and delete to the note owner only.
    """

    def has_permission(self, request, view):
        """Requires authentication for all operations."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Only the note owner can modify or delete."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
