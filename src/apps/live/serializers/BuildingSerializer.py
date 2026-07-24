"""
Esup-Pod - Building serializer.
"""

from rest_framework import serializers
from src.apps.live.models import Building


class BuildingSerializer(serializers.ModelSerializer):
    """Serializer for the Building model."""

    headband_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Building serializer metadata."""

        model = Building
        fields = ["id", "name", "headband", "headband_url", "gmapurl", "sites"]

    def get_headband_url(self, obj: Building) -> str:
        """Return the resolved headband image URL."""
        return obj.get_headband_url()
