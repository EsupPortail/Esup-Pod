from rest_framework import serializers, viewsets
from .models import BBB_Meeting, Attendee, Livestream


class MeetingModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BBB_Meeting
        fields = (
            "id",
            "meeting_id",
            "internal_meeting_id",
            "meeting_name",
            "encoding_step",
            "recorded",
            "recording_available",
            "recording_url",
            "thumbnail_url",
            "encoded_by",
            "session_date",
            "last_date_in_progress",
        )


class MeetingModelViewSet(viewsets.ModelViewSet):
    queryset = BBB_Meeting.objects.all()
    serializer_class = MeetingModelSerializer


class AttendeeModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Attendee
        fields = ("id", "full_name", "role", "username", "meeting", "user")


class AttendeeModelViewSet(viewsets.ModelViewSet):
    queryset = Attendee.objects.all()
    serializer_class = AttendeeModelSerializer


class LivestreamModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Livestream
        fields = (
            "id",
            "meeting",
            "start_date",
            "end_date",
            "show_chat",
            "download_meeting",
            "enable_chat",
            "is_restricted",
            "broadcaster_id",
            "redis_hostname",
            "redis_port",
            "redis_channel",
            "status",
            "server",
            "user",
        )
        filter_fields = ("status", "server")


class LivestreamModelViewSet(viewsets.ModelViewSet):
    queryset = Livestream.objects.all()
    serializer_class = LivestreamModelSerializer
    filter_fields = ("status", "server")
