"""
Esup-Pod - VideoAccessToken serializer.
"""

from datetime import timedelta

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from src.apps.video.conf import video_settings
from src.apps.video.models import VideoAccessToken


class VideoAccessTokenSerializer(serializers.ModelSerializer):
    """Serializer for creating and reading VideoAccessToken instances."""

    is_valid = serializers.SerializerMethodField()
    token_url = serializers.SerializerMethodField()

    class Meta:
        """Meta options for VideoAccessTokenSerializer."""

        model = VideoAccessToken
        fields = [
            "id",
            "token",
            "video",
            "label",
            "expires_at",
            "is_active",
            "is_valid",
            "use_count",
            "last_used_at",
            "created_at",
            "token_url",
        ]
        read_only_fields = [
            "id",
            "token",
            "is_valid",
            "use_count",
            "last_used_at",
            "created_at",
            "token_url",
        ]

    def get_is_valid(self, obj):
        """Returns whether the token is currently valid."""
        return obj.is_valid()

    def get_token_url(self, obj):
        """Builds the absolute URL for accessing the video via this token."""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/video/token/{obj.token}/")
        return f"/video/token/{obj.token}/"

    def validate_expires_at(self, value):
        """Ensures the expiry date is in the future and within max validity."""
        if value and value <= timezone.now():
            raise serializers.ValidationError(_("Expiry date must be in the future."))
        max_days = video_settings.video_token_max_validity_days
        if value and value > timezone.now() + timedelta(days=max_days):
            raise serializers.ValidationError(
                _("Expiry date cannot exceed %(days)s days from now.")
                % {"days": max_days}
            )
        return value
