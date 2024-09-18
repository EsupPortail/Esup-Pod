"""REST API for the Meeting module."""

from rest_framework import serializers, viewsets
from .models import InternalRecording, LiveGateway, Livestream, Meeting


class MeetingModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Meeting
        fields = (
            "id",
            "name",
            "meeting_id",
            "start_at",
            "created_at",
            "owner_id",
            "is_personal",
            "is_webinar",
            "site_id",
        )


class MeetingModelViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingModelSerializer


class InternalRecordingModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InternalRecording
        fields = ("id", "name", "start_at", "recording_id", "meeting", "site_id")


class InternalRecordingModelViewSet(viewsets.ModelViewSet):
    queryset = InternalRecording.objects.all()
    serializer_class = InternalRecordingModelSerializer


class LivestreamModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Livestream
        fields = ("id", "meeting", "status", "event", "live_gateway_id")
        filterset_fields = ["status"]


class LivestreamModelViewSet(viewsets.ModelViewSet):
    queryset = Livestream.objects.all()
    serializer_class = LivestreamModelSerializer
    filterset_fields = ["status"]


class LiveGatewayModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LiveGateway
        fields = (
            "id",
            "rtmp_stream_url",
            "broadcaster_id",
            "site_id",
        )
        filterset_fields = ["site_id"]


class LiveGatewayModelViewSet(viewsets.ModelViewSet):
    queryset = LiveGateway.objects.all()
    serializer_class = LiveGatewayModelSerializer
    filterset_fields = ["site_id"]
