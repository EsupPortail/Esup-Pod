"""
Esup-Pod - Live permissions.
"""

from rest_framework import permissions

from src.apps.live.conf import live_settings


class CanManageEvent(permissions.BasePermission):
    """
    Grant write access to users who can manage events:
    - Superusers
    - Users whose affiliation matches AFFILIATION_EVENT
    - Members of the EVENT_GROUP_ADMIN group
    """

    def has_permission(self, request, view) -> bool:
        """Allow read access to all; restrict write to event managers."""
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return _can_manage_event(request.user)

    def has_object_permission(self, request, view, obj) -> bool:
        """Allow read access; restrict write to owner or additional owners."""
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return obj.owner == request.user or request.user in obj.additional_owners.all()


class IsEventOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level: only the event owner, additional owners, or superusers
    may perform write operations.
    """

    def has_object_permission(self, request, view, obj) -> bool:
        """Allow read access; restrict write to event owner, additional owners, or superusers."""
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return obj.owner == request.user or request.user in obj.additional_owners.all()


class CanPilotBroadcaster(permissions.BasePermission):
    """
    Allow start/stop recording actions only to:
    - Superusers
    - Members of the broadcaster's manage_groups
    """

    def has_object_permission(self, request, view, obj) -> bool:
        """Allow piloting only to superusers and broadcaster manage_groups members."""
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        user_groups = request.user.groups.all()
        return obj.manage_groups.filter(pk__in=user_groups).exists()


def _can_manage_event(user) -> bool:
    """Return True if the user is allowed to create/manage events."""
    if user.is_superuser:
        return True
    if user.groups.filter(name=live_settings.event_group_admin).exists():
        return True
    try:
        affiliations = [ag.code_name for ag in user.owner.accessgroup_set.all()]
        return any(a in live_settings.affiliation_event for a in affiliations)
    except Exception:
        return False
