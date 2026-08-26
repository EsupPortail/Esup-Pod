"""
Esup-Pod - ExternalRecording serializer.
"""

import re
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from src.apps.import_video.models import ExternalRecording


class ExternalRecordingSerializer(serializers.ModelSerializer):
    """Serializer for the ExternalRecording model."""

    owner = serializers.ReadOnlyField(source="owner.username")
    import_status_label = serializers.CharField(
        source="get_import_status_display", read_only=True
    )
    source_type_label = serializers.CharField(
        source="get_source_type_display", read_only=True
    )

    class Meta:
        """ExternalRecording serializer metadata."""

        model = ExternalRecording
        fields = [
            "id",
            "name",
            "owner",
            "site",
            "source_type",
            "source_type_label",
            "source_url",
            "import_status",
            "import_status_label",
            "video",
            "error_message",
            "start_at",
            "imported_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "import_status",
            "import_status_label",
            "source_type_label",
            "video",
            "error_message",
            "start_at",
            "imported_at",
        ]

    def validate_source_url(self, value):
        """Ensures the source URL is not empty."""
        if not value:
            raise serializers.ValidationError(_("Source URL is required."))
        return value

    def validate(self, data):
        """Ensures source_type and source_url are consistent."""
        source_type = data.get("source_type")
        source_url = data.get("source_url", "")

        if source_type == ExternalRecording.SourceType.YOUTUBE:
            is_youtube = re.match(
                r"^https?://([^/]+\.)?(youtube\.[a-z]+|youtu\.be|yt\.be)/", source_url
            )
            if not is_youtube:
                raise serializers.ValidationError(
                    {"source_url": _("URL must be a valid YouTube URL.")}
                )
        elif source_type == ExternalRecording.SourceType.PEERTUBE:
            if "/videos/watch/" not in source_url and "/w/" not in source_url:
                raise serializers.ValidationError(
                    {"source_url": _("URL must be a valid PeerTube video URL.")}
                )
        elif source_type == ExternalRecording.SourceType.BBB:
            if (
                "playback/presentation" not in source_url
                and "recordID=" not in source_url
            ):
                raise serializers.ValidationError(
                    {"source_url": _("URL must be a valid BigBlueButton recording URL.")}
                )

        return data
