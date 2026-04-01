"""
Esup-Pod - Tag serializer.
"""

from rest_framework import serializers
from src.apps.video.models import Video

TagModel = Video.tags.tag_model


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        """Tag serializer metadata."""

        model = TagModel
        fields = ["id", "name", "slug", "count"]
