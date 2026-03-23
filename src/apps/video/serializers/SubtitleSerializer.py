"""
Esup-Pod - Video subtitle serializer.
"""

from rest_framework import serializers
from src.apps.video.models import Subtitle


class SubtitleSerializer(serializers.ModelSerializer):
    """
    Esup-Pod - Serializer for the Subtitle model.
    """

    class Meta:
        model = Subtitle
        fields = ["id", "video", "language", "file", "is_default"]
