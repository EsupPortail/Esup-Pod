"""
Esup-Pod - Dressing serializers.
"""

from rest_framework import serializers
from django.utils.translation import gettext as _
from src.apps.dressing.models import Dressing
from src.apps.dressing.conf import dressing_settings
from src.apps.utils.models import CustomImageModel


class CustomImageSerializer(serializers.ModelSerializer):
    """Serializer for CustomImageModel watermark images."""

    class Meta:
        """Meta options for CustomImageSerializer."""

        model = CustomImageModel
        fields = ["id", "file", "created_by"]
        read_only_fields = ["id", "created_by"]


class DressingSerializer(serializers.ModelSerializer):
    """Serializer for the Dressing model."""

    class Meta:
        """Meta options for DressingSerializer."""

        model = Dressing
        fields = [
            "id",
            "title",
            "owners",
            "users",
            "allow_to_groups",
            "watermark",
            "position",
            "opacity",
            "opening_credits",
            "ending_credits",
            "videos",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_watermark(self, value):
        """Validate the watermark image size based on max_watermark_size_mb settings."""
        if value:
            max_size_bytes = dressing_settings.max_watermark_size_mb * 1024 * 1024
            if value.file_exist() and value.file_size > max_size_bytes:
                raise serializers.ValidationError(
                    _("Watermark image size exceeds the limit of %(limit)s MB.")
                    % {"limit": dressing_settings.max_watermark_size_mb}
                )
        return value

    def _validate_credits(self, value, error_message):
        """Validate that the credits video duration does not exceed the allowed limit."""
        if value and value.duration:
            if value.duration > dressing_settings.max_credits_duration_seconds:
                raise serializers.ValidationError(
                    error_message
                    % {"limit": dressing_settings.max_credits_duration_seconds}
                )
        return value

    def validate_opening_credits(self, value):
        """Validate that the opening credits video duration does not exceed the allowed limit."""
        return self._validate_credits(
            value,
            _("Opening credits video duration exceeds the limit of %(limit)s seconds."),
        )

    def validate_ending_credits(self, value):
        """Validate that the ending credits video duration does not exceed the allowed limit."""
        return self._validate_credits(
            value,
            _("Ending credits video duration exceeds the limit of %(limit)s seconds."),
        )
