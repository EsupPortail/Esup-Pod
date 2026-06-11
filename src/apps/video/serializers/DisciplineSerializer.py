"""
Esup-Pod - Discipline serializer.
"""

from rest_framework import serializers
from src.apps.video.models import Discipline


class DisciplineSerializer(serializers.ModelSerializer):
    """
    Serializer for the Discipline model.
    """

    class Meta:
        """Discipline serializer metadata."""

        model = Discipline
        fields = ["id", "title", "slug", "description", "icon", "sites"]
