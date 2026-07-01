"""
Esup-Pod - UserMarkerTime serializer.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from src.apps.video.models import UserMarkerTime


class UserMarkerTimeSerializer(serializers.ModelSerializer):
    """Serializer for the UserMarkerTime model."""

    class Meta:
        """Meta options for UserMarkerTimeSerializer."""

        model = UserMarkerTime
        fields = ["id", "video", "marker", "updated_at"]
        read_only_fields = ["id", "updated_at"]

    def validate_marker(self, value):
        """Validates that the marker position is positive."""
        if value < 0:
            raise serializers.ValidationError(
                _("Marker position must be a positive integer.")
            )
        return value
