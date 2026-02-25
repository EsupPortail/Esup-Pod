from rest_framework import permissions
from .conf import video_settings


class IsOwnerOrCoOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Read (GET, HEAD, OPTIONS) allowed for everyone (depending on the view).
    - Write (PUT, PATCH, DELETE) allowed only for the owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if video_settings.restrict_edit_to_staff:
            return request.user and (request.user.is_staff or request.user.is_superuser)
        is_owner = obj.owner == request.user
        is_staff = request.user.is_staff or request.user.is_superuser
        is_co_owner = request.user in obj.co_owners.all()
        if request.method == 'DELETE':
            return is_owner or is_staff
        return is_owner or is_co_owner or is_staff
