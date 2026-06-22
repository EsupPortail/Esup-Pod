"""
Esup-Pod - Overlay serializer.
"""

from rest_framework import serializers
from src.apps.completion.models import Overlay
import re
from src.apps.completion.conf import completion_settings


class OverlaySerializer(serializers.ModelSerializer):
    """Serializer for the Overlay model."""

    class Meta:
        """Meta options for OverlaySerializer."""

        model = Overlay
        fields = [
            "id",
            "video",
            "title",
            "time_start",
            "time_end",
            "content",
        ]

    def validate(self, attrs):
        """
        Validate timestamps logic via model's clean method,
        and handle link superposition if enabled.
        """
        # Merge with existing instance data for partial updates
        if self.instance:
            data = {
                "video_id": self.instance.video_id,
                "title": self.instance.title,
                "time_start": self.instance.time_start,
                "time_end": self.instance.time_end,
                "content": self.instance.content,
            }
            data.update(attrs)
            instance = Overlay(**data)
            instance.pk = self.instance.pk
        else:
            instance = Overlay(**attrs)

        instance.clean()

        # Handle LINK_SUPERPOSITION
        if completion_settings.link_superposition:
            content = attrs.get("content", "")
            if content:
                url_pattern = re.compile(r'(?<!href=")(?<!src=")(https?://[^\s<]+)')
                attrs["content"] = url_pattern.sub(
                    r'<a href="\1" target="_blank">\1</a>', content
                )

        return attrs
