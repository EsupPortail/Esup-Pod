from rest_framework import serializers
from src.apps.video.models import Video
from .SubtitleSerializer import SubtitleSerializer


class VideoSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    video_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Video
        fields = ['id', 'title', 'slug', 'description', 'video_file', 'owner', 'duration', 'status', 'status_label', 'created_at', 'video_url', 'subtitles',]
        read_only_fields = ['slug', 'created_at', 'duration', 'owner', 'status_label']
        subtitles = SubtitleSerializer(many=True, read_only=True)

    def get_video_url(self, obj):
        request = self.context.get('request')
        if obj.video_file and hasattr(obj.video_file, 'url'):
            if request:
                return request.build_absolute_uri(obj.video_file.url)
            return obj.video_file.url
        return None
