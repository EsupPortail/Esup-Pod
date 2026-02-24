from rest_framework import permissions
from .conf import video_settings


class IsOwnerOrCoOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée :
    - Lecture (GET, HEAD, OPTIONS) autorisée pour tout le monde (selon la vue).
    - Écriture (PUT, PATCH, DELETE) autorisée uniquement pour le propriétaire.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if video_settings.restrict_edit_to_staff and not request.user.is_staff:
            return False
        return (
            obj.owner == request.user
            or obj.co_owners.filter(pk=request.user.pk).exists()
            or request.user.is_superuser
        )
