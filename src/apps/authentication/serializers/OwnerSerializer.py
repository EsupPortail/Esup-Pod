from django.contrib.auth import get_user_model
from rest_framework import serializers

from ..models.Owner import Owner

User = get_user_model()


class OwnerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Owner
        fields = (
            "id",
            "user",
            "auth_type",
            "affiliation",
            "comment",
            "hashkey",
            "userpicture",
            "sites",
        )


class OwnerWithGroupsSerializer(serializers.ModelSerializer):
    """
    Specific serializer including AccessGroups.
    Used in particular when modifying a user's permissions.
    """

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Owner
        fields = (
            "id",
            "user",
            "auth_type",
            "affiliation",
            "comment",
            "hashkey",
            "userpicture",
            "accessgroups",
        )
