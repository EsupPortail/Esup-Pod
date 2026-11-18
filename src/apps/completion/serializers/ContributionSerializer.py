"""
Esup-Pod - Contribution serializer.
"""

from rest_framework import serializers
from src.apps.completion.models import Contribution, Role
from .ContributorSerializer import ContributorSerializer


class ContributionSerializer(serializers.ModelSerializer):
    """Serializer for the Contribution model."""

    role = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Role.objects.filter(is_active=True),
    )

    contributor_details = ContributorSerializer(source="contributor", read_only=True)
    contributor_id = serializers.PrimaryKeyRelatedField(
        source="contributor",
        queryset=ContributorSerializer.Meta.model.objects.all(),
        write_only=True,
    )

    class Meta:
        """Meta options for ContributionSerializer."""

        model = Contribution
        fields = [
            "id",
            "video",
            "contributor_id",
            "contributor_details",
            "role",
            "job_title",
        ]
