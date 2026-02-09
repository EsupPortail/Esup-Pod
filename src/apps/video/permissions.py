from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée :
    - Lecture (GET, HEAD, OPTIONS) autorisée pour tout le monde (selon la vue).
    - Écriture (PUT, PATCH, DELETE) autorisée uniquement pour le propriétaire.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.owner == request.user
