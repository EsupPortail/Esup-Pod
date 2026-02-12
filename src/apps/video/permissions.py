from rest_framework import permissions


class IsOwnerOrCoOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée :
    - Lecture (GET, HEAD, OPTIONS) autorisée pour tout le monde (selon la vue).
    - Écriture (PUT, PATCH, DELETE) autorisée uniquement pour le propriétaire.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if obj.owner == request.user:
            return True
        if obj.co_owners.filter(pk=request.user.pk).exists():
            if request.method == "DELETE":
                return False
            return True
        return False
