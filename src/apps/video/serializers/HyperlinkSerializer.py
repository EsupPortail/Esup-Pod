"""
Esup-Pod - Serializer for the VideoHyperlink model.
"""

from rest_framework import serializers
from src.apps.video.models import VideoHyperlink


class VideoHyperlinkSerializer(serializers.ModelSerializer):
    """
    Esup-Pod - Serializes VideoHyperlink instances for API input and output.
    """

    class Meta:
        """Metadata for the VideoHyperlinkSerializer."""

        model = VideoHyperlink
        fields = [
            "id",
            "video",
            "url",
            "text",
            "icon",
            "position",
            "time_start",
            "time_end",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
