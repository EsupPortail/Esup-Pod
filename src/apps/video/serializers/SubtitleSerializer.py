"""
Esup-Pod - Video subtitle serializer.
"""

from rest_framework import serializers
from src.apps.video.models import Subtitle


class SubtitleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Subtitle model.
    """

    class Meta:
        """Subtitle serializer metadata."""

        model = Subtitle
        fields = ["id", "video", "language", "file", "is_default"]
