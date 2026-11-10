"""
Esup-Pod - Role serializer.
"""

from rest_framework import serializers
from src.apps.completion.models import Role


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for the Role model."""

    class Meta:
        """Role serializer metadata."""

        model = Role
        fields = [
            "code",
            "label",
            "is_active",
            "order",
        ]
