"""
Esup-Pod - Broadcaster serializer.
"""

from rest_framework import serializers
from src.apps.live.models import Broadcaster


class BroadcasterSerializer(serializers.ModelSerializer):
    """
    Read serializer for the Broadcaster model.

    The piloting_conf field is intentionally excluded from the
    public representation as it may contain credentials.
    Staff users can view it via the Django admin.
    """

    poster_url = serializers.SerializerMethodField(read_only=True)
    is_recording = serializers.SerializerMethodField(read_only=True)
    qrcode = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Broadcaster serializer metadata."""

        model = Broadcaster
        fields = [
            "id",
            "name",
            "slug",
            "building",
            "description",
            "poster",
            "poster_url",
            "url",
            "status",
            "enable_add_event",
            "enable_viewer_count",
            "is_restricted",
            "public",
            "manage_groups",
            "piloting_implementation",
            "main_lang",
            "is_recording",
            "qrcode",
        ]
        read_only_fields = ["slug", "is_recording", "qrcode"]
        # piloting_conf is intentionally excluded (may contain credentials)
        lookup_field = "slug"

    def get_poster_url(self, obj: Broadcaster) -> str:
        """Return the resolved poster image URL."""
        return obj.get_poster_url()

    def get_is_recording(self, obj: Broadcaster) -> bool:
        """Return whether the broadcaster is currently recording."""
        return obj.is_recording()

    def get_qrcode(self, obj: Broadcaster) -> str:
        """Return the QR code data-URI for immediate event creation."""
        return obj.qrcode
