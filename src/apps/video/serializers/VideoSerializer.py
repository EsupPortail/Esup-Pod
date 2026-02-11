from rest_framework import serializers
from src.apps.video.models import Video
from .SubtitleSerializer import SubtitleSerializer


class VideoSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    video_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "video_file",
            "thumbnail",
            "duration",
            "is_360",
            "is_video",
            "owner",
            "co_owners",
            "status",
            "status_label",
            "password",
            "allow_downloading",
            "disable_comment",
            "date_of_event",
            "license",
            "cursus",
            "language",
            "created_at",
            "updated_at",
            "date_to_delete",
            "video_url",
        ]
        read_only_fields = [
            "slug",
            "created_at",
            "updated_at",
            "duration",
            "owner",
            "status_label",
        ]
        subtitles = SubtitleSerializer(many=True, read_only=True)

    def get_video_url(self, obj):
        request = self.context.get("request")
        if obj.video_file and hasattr(obj.video_file, "url"):
            if request:
                return request.build_absolute_uri(obj.video_file.url)
            return obj.video_file.url
        return None
