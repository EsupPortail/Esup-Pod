"""
Esup-Pod - Video serializer.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from src.apps.video.models import Video
from .SubtitleSerializer import SubtitleSerializer
from django.contrib.auth.hashers import make_password
from src.apps.encoding.conf import encoding_settings
from src.apps.video.conf import video_settings

User = get_user_model()


class VideoSerializer(serializers.ModelSerializer):
    """
    Esup-Pod - Serializer for the Video model.
    """

    owner = serializers.ReadOnlyField(source="owner.username")
    owner_id = serializers.ReadOnlyField(source="owner.id")
    video_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    has_password = serializers.BooleanField(source="password", read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    subtitles = SubtitleSerializer(many=True, read_only=True)
    co_owners = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    date_of_event = serializers.DateField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    date_to_delete = serializers.DateField(required=False, allow_null=True)
    thumbnail_url = serializers.ReadOnlyField()

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "video_file",
            "video_url",
            "thumbnail",
            "duration",
            "is_360",
            "is_video",
            "owner",
            "owner_id",
            "co_owners",
            "status",
            "status_label",
            "is_auth_required",
            "password",
            "thumbnail_url",
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
        extra_kwargs = {
            "video_file": {"write_only": True},
        }
        read_only_fields = [
            "slug",
            "created_at",
            "updated_at",
            "duration",
            "owner",
            "owner_id",
            "status_label",
            "subtitles",
        ]

    def validate_password(self, value):
        """Hashes the password if it is provided."""
        if value:
            return make_password(value)
        return value

    def get_video_url(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        is_privileged = (
            user
            and user.is_authenticated
            and (
                user.is_superuser
                or obj.owner == user
                or obj.co_owners.filter(pk=user.pk).exists()
            )
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
        if file_field and hasattr(file_field, "url"):
            if request:
                return request.build_absolute_uri(file_field.url)
            return file_field.url
        return None

    def validate_video_file(self, value):
        if value:
            ext = value.name.split(".")[-1].lower()
            allowed_exts = [e.lstrip(".") for e in encoding_settings.allowed_extensions]
            if ext not in allowed_exts:
                raise serializers.ValidationError(
                    f"Unsupported format. Allowed formats: {', '.join(allowed_exts)}"
                )
            max_bytes = encoding_settings.max_upload_size_gb * 1024 * 1024 * 1024
            if value.size > max_bytes:
                raise serializers.ValidationError(
                    f"The file exceeds the maximum allowed size of {encoding_settings.max_upload_size_gb} GB."
                )
        return value

    def validate(self, attrs):
        """
        Global validation to handle WEBTV_MODE.
        """
        attrs = super().validate(attrs)
        has_video_file_in_req = "video_file" in attrs and attrs["video_file"] is not None
        already_has_file = bool(self.instance.video_file) if self.instance else False
        is_clearing_file = "video_file" in attrs and attrs["video_file"] is None
        has_file_after_update = (
            already_has_file and not is_clearing_file
        ) or has_video_file_in_req
        final_status = attrs.get(
            "status", self.instance.status if self.instance else None
        )
        if not video_settings.webtv_mode:
            if not has_file_after_update:
                raise serializers.ValidationError(
                    {
                        "video_file": "A video file is required because WEBTV mode is disabled."
                    }
                )
            if final_status == Video.Status.PUBLISHED and not has_file_after_update:
                raise serializers.ValidationError(
                    {
                        "status": "Cannot publish a video that has no source file (WebTV mode disabled)."
                    }
                )
        return attrs
