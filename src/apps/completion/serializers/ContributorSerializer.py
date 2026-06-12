"""
Esup-Pod - Contributor serializer.
"""

from rest_framework import serializers
from src.apps.completion.models import Contributor


class ContributorSerializer(serializers.ModelSerializer):
    """Serializer for the Contributor model."""

    full_name = serializers.ReadOnlyField()

    class Meta:
        """Meta options for ContributorSerializer."""

        model = Contributor
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email_address",
            "weblink",
            "created_at",
        ]
