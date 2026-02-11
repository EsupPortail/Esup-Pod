from django.contrib.auth import get_user_model
from rest_framework import serializers
from src.apps.video.models import Video
from .SubtitleSerializer import SubtitleSerializer
from django.contrib.auth.hashers import make_password
User = get_user_model()


class VideoSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    video_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    has_password = serializers.BooleanField(source='password', read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    subtitles = SubtitleSerializer(many=True, read_only=True)
    co_owners = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False
    )

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "video_url",
            "thumbnail",
            "duration",
            "is_360",
            "is_video",
            "owner",
            "co_owners",
            "status",
            "status_label",
            "is_auth_required",
            "password",
            "has_password",
            "subtitles",
            "allow_downloading",
            "disable_comment",
            "date_of_event",
            "license",
            "cursus",
            "language",
            "created_at",
            "updated_at",
            "date_to_delete",
        ]
        read_only_fields = [
            "slug",
            "created_at",
            "updated_at",
            "duration",
            "owner",
            "status_label",
            "subtitles"
        ]

    def validate_password(self, value):
        """Hash le mot de passe s'il est fourni."""
        if value:
            return make_password(value)
        return value

    def get_video_url(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        is_privileged = (
            user and user.is_authenticated
            and (user.is_superuser or obj.owner == user or obj.co_owners.filter(pk=user.pk).exists())
        )
        if is_privileged:
            return self._get_absolute_url(obj.video_file, request)
        if not obj.allow_downloading:
            return None
        if obj.status == Video.Status.RESTRICTED:
            if obj.password:
                return None
            if obj.is_auth_required and (not user or not user.is_authenticated):
                return None
        return self._get_absolute_url(obj.video_file, request)

    def _get_absolute_url(self, file_field, request):
        if file_field and hasattr(file_field, 'url'):
            if request:
                return request.build_absolute_uri(file_field.url)
            return file_field.url
        return None
