"""
Esup-Pod - VideoCut serializer.
"""

from rest_framework import serializers
from src.apps.video.models import VideoCut


from django.utils.translation import gettext_lazy as _


class VideoCutSerializer(serializers.ModelSerializer):
    """Serializer for the VideoCut model."""

    class Meta:
        """VideoCut serializer metadata."""

        model = VideoCut
        fields = ["id", "time_start", "time_end", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        """Ensures time_start is strictly less than time_end."""
        if data.get("time_start", 0) >= data.get("time_end", 0):
            raise serializers.ValidationError(
                _("Start time must be strictly less than end time.")
            )
        return data
