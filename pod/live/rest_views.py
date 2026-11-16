"""Esup-Pod Live API serializers and views."""

from .models import Building, Broadcaster, Event
from rest_framework import serializers, viewsets
from rest_framework.validators import UniqueValidator
from django.core.exceptions import ValidationError
from pod.video_encode_transcript.models import RunnerManager

# Serializers define the API representation.
from django.conf import settings

USE_LIVE_TRANSCRIPTION = getattr(settings, "USE_LIVE_TRANSCRIPTION", False)
if USE_LIVE_TRANSCRIPTION:
    from pod.live.live_transcript import transcribe_live


class BuildingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Building
        fields = ("id", "url", "name", "headband", "gmapurl", "sites")


class BroadcasterSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="broadcaster-detail", lookup_field="slug"
    )
    broadcaster_url = serializers.URLField(
        source="url",
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[UniqueValidator(queryset=Broadcaster.objects.all())],
    )
    runner_manager = serializers.PrimaryKeyRelatedField(
        queryset=RunnerManager.objects.filter(supports_live=True),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        """Validate the effective stream configuration, including partial updates."""
        fields = ("stream_mode", "url", "runner_manager", "source_id", "building")
        values = {
            field: attrs.get(field, getattr(self.instance, field, None))
            for field in fields
            if field in attrs or self.instance is not None
        }
        candidate = Broadcaster(**values)
        try:
            candidate.clean()
        except ValidationError as exc:
            errors = exc.message_dict
            if "url" in errors:
                errors["broadcaster_url"] = errors.pop("url")
            raise serializers.ValidationError(errors)
        return attrs

    def to_representation(self, instance):
        """Expose the resolved playback URL without serializing manager credentials."""
        data = super().to_representation(instance)
        data["broadcaster_url"] = instance.get_stream_url() or None
        return data

    class Meta:
        model = Broadcaster
        fields = (
            "id",
            "url",
            "name",
            "slug",
            "building",
            "description",
            "poster",
            "broadcaster_url",
            "stream_mode",
            "runner_manager",
            "source_id",
            "status",
            "is_restricted",
            "manage_groups",
            "piloting_implementation",
            "piloting_conf",
        )
        lookup_field = "slug"


class EventSerializer(serializers.HyperlinkedModelSerializer):
    broadcaster = serializers.HyperlinkedRelatedField(
        view_name="broadcaster-detail",
        queryset=Broadcaster.objects.all(),
        many=False,
        read_only=False,
        lookup_field="slug",
    )

    class Meta:
        model = Event
        fields = (
            "id",
            "url",
            "title",
            "owner",
            "additional_owners",
            "slug",
            "description",
            "start_date",
            "end_date",
            "broadcaster",
            "type",
            "is_draft",
            "is_restricted",
            "is_auto_start",
            "videos",
            "thumbnail",
            "video_on_hold",
            "enable_transcription",
        )


#############################################################################
# ViewSets define the view behavior.
#############################################################################


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all().order_by("name")
    serializer_class = BuildingSerializer


class BroadcasterViewSet(viewsets.ModelViewSet):
    queryset = Broadcaster.objects.select_related("runner_manager").order_by(
        "building", "name"
    )
    serializer_class = BroadcasterSerializer
    lookup_field = "slug"
    filterset_fields = ["source_id"]

    def partial_update(self, request, *args, **kwargs):
        data_updated = super().partial_update(request, *args, **kwargs)
        if USE_LIVE_TRANSCRIPTION and data_updated.status_code == 200:
            broadcaster = Broadcaster.objects.get(slug=kwargs["slug"])
            events = Event.objects.filter(
                broadcaster=broadcaster, enable_transcription=True
            )
            if events:
                transcribe_live(
                    broadcaster.url,
                    broadcaster.slug,
                    request.data.get("status"),
                    broadcaster.main_lang,
                    broadcaster.transcription_file.path,
                )
        return data_updated


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by("start_date")
    serializer_class = EventSerializer
