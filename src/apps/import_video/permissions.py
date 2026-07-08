"""
Esup-Pod - Import Video permissions.
"""

from rest_framework import permissions
from src.apps.import_video.conf import import_video_settings


class CanImportVideo(permissions.BasePermission):
    """
    Allows access to authenticated users.
    If restrict_to_staff is enabled, only staff users can create or import.
    """

    def has_permission(self, request, view):
        """Grants read access to authenticated users, write access based on staff restriction."""
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if import_video_settings.restrict_to_staff:
            return (
                request.user.is_staff
                or request.user.is_superuser
                or (
                    hasattr(request.user, "owner")
                    and request.user.owner.server_roles.filter(
                        can_import_video=True
                    ).exists()
                )
            )
        return True
