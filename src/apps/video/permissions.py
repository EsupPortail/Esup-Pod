from rest_framework import permissions
from src.apps.video.services.core import RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY


class IsOwnerOrCoOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée :
    - Lecture (GET, HEAD, OPTIONS) autorisée pour tout le monde (selon la vue).
    - Écriture (PUT, PATCH, DELETE) autorisée uniquement pour le propriétaire.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and not request.user.is_staff:
            return False
        return (
            obj.owner == request.user
            or obj.co_owners.filter(pk=request.user.pk).exists()
            or request.user.is_superuser
        )
