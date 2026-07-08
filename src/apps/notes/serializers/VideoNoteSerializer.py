"""
Esup-Pod - VideoNote serializer.
"""

from rest_framework import serializers
from src.apps.notes.models import VideoNote


class VideoNoteSerializer(serializers.ModelSerializer):
    """Serializer for the VideoNote model."""

    owner = serializers.ReadOnlyField(source="owner.username")
    privacy_label = serializers.CharField(source="get_privacy_display", read_only=True)

    class Meta:
        """VideoNote serializer metadata."""

        model = VideoNote
        fields = [
            "id",
            "video",
            "owner",
            "content",
            "timestamp",
            "privacy",
            "privacy_label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "privacy_label", "created_at", "updated_at"]

    def validate_timestamp(self, value):
        """Ensures timestamp is positive if provided."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Timestamp must be a positive integer.")
        return value
