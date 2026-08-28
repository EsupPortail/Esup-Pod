"""
Esup-Pod - Event serializer.
"""

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from src.apps.live.models import Event


class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for the Event model.

    Handles both read and write operations.
    On write, only the owner (or staff) may set sensitive fields.
    """

    owner = serializers.StringRelatedField(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField(read_only=True)
    viewer_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Event serializer metadata."""

        model = Event
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "owner",
            "additional_owners",
            "start_date",
            "end_date",
            "broadcaster",
            "type",
            "is_draft",
            "is_restricted",
            "restrict_access_to_groups",
            "is_auto_start",
            "is_recording_stopped",
            "iframe_url",
            "iframe_height",
            "aside_iframe_url",
            "video_on_hold",
            "thumbnail",
            "thumbnail_url",
            "max_viewers",
            "videos",
            "enable_transcription",
            "status",
            "viewer_count",
        ]
        read_only_fields = [
            "slug",
            "owner",
            "is_recording_stopped",
            "max_viewers",
            "videos",
            "status",
            "viewer_count",
            "thumbnail_url",
        ]

    def get_status(self, obj: Event) -> str:
        """Return the temporal status of the event: 'coming', 'current', or 'past'."""
        if obj.is_current():
            return "current"
        if obj.is_past():
            return "past"
        return "coming"

    def get_thumbnail_url(self, obj: Event) -> str:
        """Return the resolved thumbnail URL."""
        return obj.get_thumbnail_url()

    def get_viewer_count(self, obj: Event) -> int:
        """Return the current number of active heartbeats (live viewer count)."""
        from src.apps.live.conf import live_settings
        from src.apps.live.models import HeartBeat

        HeartBeat.cleanup_stale(obj, live_settings.heartbeat_delay)
        return obj.heartbeats.count()

    def validate(self, attrs):
        """Ensure end_date is after start_date and start_date is not in the past (for non-admin users)."""
        from django.utils import timezone as tz

        request = self.context.get("request")
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))

        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_date": _("End date must be after start date.")}
            )

        # Mirror V4 present_or_future_date: prevent scheduling events in the past
        # (allowed for superusers/staff who may need to backfill)
        if start and not self.instance:  # only on creation
            is_privileged = (
                request
                and request.user.is_authenticated
                and (request.user.is_superuser or request.user.is_staff)
            )
            if not is_privileged and start < tz.now().replace(second=0, microsecond=0):
                raise serializers.ValidationError(
                    {"start_date": _("An event cannot be planned in the past.")}
                )

        return attrs
