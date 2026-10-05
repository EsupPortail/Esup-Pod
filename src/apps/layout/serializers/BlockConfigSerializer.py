"""
Esup-Pod - BlockConfig serializers.
"""

from rest_framework import serializers
from src.apps.layout.models import BlockConfig


class BlockConfigSerializer(serializers.ModelSerializer):
    """Serializer for BlockConfig."""

    class Meta:
        """Meta options."""

        model = BlockConfig
        fields = [
            "frontend_id",
            "is_active",
            "display_title",
            "subtitle_or_text",
            "item_limit",
            "background_color",
            "text_color",
            "extra_config",
        ]
