"""
Esup-Pod - Type serializer.
"""

from rest_framework import serializers
from src.apps.video.models import Type


class TypeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Type model.
    """

    class Meta:
        """Type serializer metadata."""

        model = Type
        fields = ["id", "title", "slug", "sites"]
