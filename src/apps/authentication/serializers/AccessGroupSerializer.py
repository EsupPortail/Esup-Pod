from rest_framework import serializers
from ..models.AccessGroup import AccessGroup


class AccessGroupSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = AccessGroup
        fields = ("id", "display_name", "code_name", "sites", "users", "auto_sync")
        read_only_fields = ["users"]
