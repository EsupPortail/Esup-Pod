"""
Esup-Pod - ViewCount serializer.
"""

from rest_framework import serializers

from src.apps.video.models import ViewCount


class ViewCountSerializer(serializers.ModelSerializer):
    """Serializer for daily view count data."""

    class Meta:
        """Meta options for ViewCountSerializer."""

        model = ViewCount
        fields = ["date", "count"]
        read_only_fields = ["date", "count"]
