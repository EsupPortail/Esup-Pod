"""
Esup-Pod - Collection permissions.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        """Allow read for all; restrict write to the object owner."""
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return hasattr(obj, "owner") and obj.owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow administrators to edit.
    """

    def has_permission(self, request, view):
        """Allow read for all; restrict write to staff users."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_superuser


class IsChannelOwnerOrCollaboratorOrReadOnly(permissions.BasePermission):
    """
    Custom permission for Channel model:
    - Read: Allowed for anyone if public.
    - Write: Allowed for owner and collaborators.
    - Delete: Allowed for owner and admins.
    """

    def has_object_permission(self, request, view, obj):
        """Allow read for public channels; restrict writes to owner, collaborators, and staff."""
        # 1. Safe methods
        if request.method in permissions.SAFE_METHODS:
            if getattr(obj, "is_public", True):
                return True
            return request.user.is_authenticated and (
                obj.owner == request.user
                or obj.collaborators.filter(pk=request.user.pk).exists()
            )

        # 2. Superusers have all rights (God Mode)
        if request.user and request.user.is_superuser:
            return True

        # 3. Check ownership and collaboration
        is_owner = obj.owner == request.user
        is_collaborator = obj.collaborators.filter(pk=request.user.pk).exists()

        if request.method in ["PUT", "PATCH", "POST"]:
            return is_owner or is_collaborator

        if request.method == "DELETE":
            return is_owner

        return False


class IsAdminOrThemeOwner(permissions.BasePermission):
    """
    Custom permission for Theme model:
    - Admins: Full access.
    - Others:
        - Read: Always allowed.
        - Write: Allowed if it's a channel theme, the user is the channel owner,
          and the OWNER_CAN_MANAGE_THEMES flag is enabled.
    """

    def has_permission(self, request, view):
        """Global permission check for creation and listing."""
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Check if user can create themes (only for their own channels)
        if request.method == "POST":
            from src.apps.collection.conf import collection_settings

            if not collection_settings.owner_can_manage_themes:
                return False

            channel_id = request.data.get("channel")
            if channel_id:
                from src.apps.collection.models import Channel

                try:
                    channel = Channel.objects.get(pk=channel_id)
                    return channel.owner == request.user
                except Channel.DoesNotExist:
                    return False
            return False  # Non-admins cannot create global themes (channel=null)

        return True

    def has_object_permission(self, request, view, obj):
        """Object-level permission check for editing/deleting."""
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Check channel ownership if it's a channel-specific theme
        from src.apps.collection.conf import collection_settings

        if obj.channel and collection_settings.owner_can_manage_themes:
            return obj.channel.owner == request.user

        return False
