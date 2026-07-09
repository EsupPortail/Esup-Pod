"""
Esup-Pod - Detailed user serializer.
"""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from src.apps.authentication.models import ServerRole

User = get_user_model()


class ServerRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for the ServerRole model.
    """

    class Meta:
        """ServerRoleSerializer metadata."""

        model = ServerRole
        fields = [
            "id",
            "name",
            "description",
            "scope",
            "can_delete_video",
            "can_edit_video",
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, enriched with Owner profile data.
    """

    affiliation = serializers.SerializerMethodField(method_name="get_affiliation")
    establishment = serializers.SerializerMethodField(method_name="get_establishment")
    userpicture = serializers.SerializerMethodField(method_name="get_userpicture")
    server_roles = serializers.SerializerMethodField(method_name="get_server_roles")
    is_superuser = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)

    class Meta:
        """User serializer metadata."""

        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "affiliation",
            "establishment",
            "userpicture",
            "server_roles",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_affiliation(self, obj) -> str | None:
        """Returns the user's affiliation from the Owner profile."""
        if hasattr(obj, "owner"):
            return obj.owner.affiliation
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_establishment(self, obj) -> str | None:
        """Returns the user's establishment from the Owner profile."""
        if hasattr(obj, "owner"):
            return obj.owner.establishment
        return None

    def get_userpicture(self, obj) -> str | None:
        """Retrieves the relative URL of the user's profile picture."""
        if hasattr(obj, "owner") and obj.owner.userpicture:
            return obj.owner.userpicture.url
        return None

    @extend_schema_field(ServerRoleSerializer(many=True))
    def get_server_roles(self, obj):
        """Retrieves the list of custom roles assigned to the user."""
        if hasattr(obj, "owner"):
            return ServerRoleSerializer(obj.owner.server_roles.all(), many=True).data
        return []
