"""
Esup-Pod - VideoStats serializer.
"""

from rest_framework import serializers

from .ViewCountSerializer import ViewCountSerializer


class VideoStatsSerializer(serializers.Serializer):
    """
    Read-only serializer for aggregated video statistics.
    Used by the stats endpoint to return chart-ready data.
    """

    video_slug = serializers.CharField(read_only=True)
    total_views = serializers.IntegerField(read_only=True)
    views_last_7_days = serializers.IntegerField(read_only=True)
    views_last_30_days = serializers.IntegerField(read_only=True)
    daily_breakdown = ViewCountSerializer(many=True, read_only=True)
    peak_day = serializers.DateField(allow_null=True, read_only=True)
    peak_count = serializers.IntegerField(allow_null=True, read_only=True)

    def create(self, validated_data):
        """Not used — this serializer is read-only."""
        raise NotImplementedError

    def update(self, instance, validated_data):
        """Not used — this serializer is read-only."""
        raise NotImplementedError
