"""
Esup-Pod - DublinCore serializer.
"""

from rest_framework import serializers


class DublinCoreSerializer(serializers.Serializer):
    """
    Read-only serializer exposing Dublin Core metadata for a Video.
    Maps directly to Video.get_dublin_core() output.
    """

    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    creator = serializers.CharField(read_only=True)
    publisher = serializers.CharField(read_only=True)
    date = serializers.CharField(read_only=True)
    format = serializers.CharField(read_only=True)
    rights = serializers.CharField(read_only=True)
    coverage = serializers.CharField(read_only=True)
    subject = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    language = serializers.CharField(read_only=True)
    identifier = serializers.CharField(read_only=True)

    def create(self, validated_data):
        """Not used — this serializer is read-only."""
        raise NotImplementedError

    def update(self, instance, validated_data):
        """Not used — this serializer is read-only."""
        raise NotImplementedError
