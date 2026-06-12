"""
Esup-Pod - Document serializer.
"""

from rest_framework import serializers
from src.apps.completion.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for the Document model."""

    class Meta:
        """Meta options for DocumentSerializer."""

        model = Document
        fields = [
            "id",
            "video",
            "title",
            "file",
            "is_private",
            "created_at",
        ]
