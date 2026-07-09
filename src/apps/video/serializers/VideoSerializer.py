"""
Esup-Pod - Video serializer.
"""

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from src.apps.video.models import Video, Type, Discipline
from .SubtitleSerializer import SubtitleSerializer
from django.contrib.auth.hashers import make_password
from src.apps.encoding.conf import encoding_settings
from src.apps.video.conf import video_settings
from src.apps.authentication.models import AccessGroup
from src.apps.collection.models import Theme, ThemeItem, Channel
from src.apps.completion.serializers import (
    ContributionSerializer,
    OverlaySerializer,
    DocumentSerializer,
)
from .DisciplineSerializer import DisciplineSerializer
from .HyperlinkSerializer import VideoHyperlinkSerializer

User = get_user_model()


class TagListSerializerField(serializers.Field):
    """
    Custom field for django-tagulous TagField to support read and write operations.
    """

    def get_value(self, dictionary):
        """Extracts the field value from the provided dictionary."""
        if self.field_name not in dictionary:
            return serializers.empty
        if hasattr(dictionary, "getlist"):
            return dictionary.getlist(self.field_name)
        return dictionary.get(self.field_name)

    def to_representation(self, value):
        return [tag.name for tag in value.all()]

    def to_internal_value(self, data):
        """Converts the provided data into the internal list format."""
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, str):
                    result.extend([t.strip() for t in item.split(",") if t.strip()])
                else:
                    result.append(item)
            return result
        if isinstance(data, str):
            return [tag.strip() for tag in data.split(",") if tag.strip()]
        raise serializers.ValidationError(
            "Expected a list of tags or a comma-separated string."
        )


class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer for the Video model.
    """

    owner = serializers.ReadOnlyField(source="owner.username")
    owner_id = serializers.ReadOnlyField(source="owner.id")
    owner_first_name = serializers.ReadOnlyField(source="owner.first_name")
    owner_last_name = serializers.ReadOnlyField(source="owner.last_name")
    video_url = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    encoding_status_label = serializers.CharField(
        source="get_encoding_status_display", read_only=True
    )
    has_password = serializers.SerializerMethodField()
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, allow_null=True
    )
    tags = TagListSerializerField(required=False)
    subtitles = SubtitleSerializer(many=True, read_only=True)
    encodings = serializers.SerializerMethodField()
    co_owners = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    restricted_groups = serializers.PrimaryKeyRelatedField(
        many=True, queryset=AccessGroup.objects.all(), required=False
    )
    themes = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Theme.objects.all(), required=False
    )
    channel = serializers.SlugRelatedField(
        queryset=Channel.objects.all(), slug_field="slug", required=False, allow_null=True
    )
    date_of_event = serializers.DateField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    date_to_delete = serializers.DateField(required=False, allow_null=True)
    thumbnail = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text=_(
            "The video thumbnail image. When serialized (read-only), if no manual thumbnail has been uploaded, this field dynamically falls back to the auto-generated storyboard preview ('overview') or the default static thumbnail URL."
        ),
    )
    thumbnail_url = serializers.SerializerMethodField(
        help_text=_(
            "The absolute URL of the video thumbnail, automatically falling back to the overview preview or default static thumbnail if not explicitly uploaded."
        )
    )
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=Type.objects.all(), source="type", write_only=True, required=False
    )
    type_name = serializers.CharField(source="type.title", read_only=True)
    disciplines = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Discipline.objects.all(), required=False
    )
    discipline_details = DisciplineSerializer(
        source="disciplines", many=True, read_only=True
    )

    hyperlinks = VideoHyperlinkSerializer(many=True, read_only=True)
    contributions = ContributionSerializer(many=True, read_only=True)
    overlays = OverlaySerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        """Video serializer metadata."""

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
            "owner_first_name",
            "owner_last_name",
            "co_owners",
            "status",
            "status_label",
            "encoding_status",
            "encoding_status_label",
            "is_auth_required",
            "password",
            "thumbnail_url",
            "has_password",
            "subtitles",
            "encodings",
            "allow_downloading",
            "disable_comment",
            "date_of_event",
            "license",
            "cursus",
            "language",
            "channel",
            "themes",
            "created_at",
            "updated_at",
            "date_to_delete",
            "restricted_groups",
            "type_id",
            "type_name",
            "disciplines",
            "discipline_details",
            "tags",
            "hyperlinks",
            "contributions",
            "overlays",
            "documents",
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
            "owner_first_name",
            "owner_last_name",
            "status_label",
            "encoding_status",
            "encoding_status_label",
            "subtitles",
            "encodings",
        ]

    @extend_schema_field(serializers.BooleanField())
    def get_has_password(self, obj):
        """Returns True if the video has a password, False otherwise."""
        return bool(obj.password)

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_encodings(self, obj):
        """Returns a list of available encoded resolutions (e.g., ['1080p', '720p'])."""
        return [enc.resolution for enc in obj.encodings.all()]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_thumbnail_url(self, obj):
        """Returns the absolute URL of the video thumbnail."""
        request = self.context.get("request")
        url = obj.thumbnail_url
        if url and request and not url.startswith("http"):
            return request.build_absolute_uri(url)
        return url

    def validate_password(self, value):
        """Hashes the password if it is provided."""
        if value:
            return make_password(value)
        return value

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_video_url(self, obj):
        """Calculates the absolute URL of the video file based on access rights."""
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
        """Helper to build an absolute URI for a file field."""
        if file_field and hasattr(file_field, "url"):
            if request:
                return request.build_absolute_uri(file_field.url)
            return file_field.url
        return None

    def validate_video_file(self, value):
        """Ensures the uploaded file has a valid extension and size."""
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

    def to_representation(self, instance):
        """
        Customizes representation to return the overview URL or default thumbnail
        as the 'thumbnail' field if no manual thumbnail has been uploaded.
        """
        data = super().to_representation(instance)
        if not data.get("thumbnail"):
            data["thumbnail"] = data.get("thumbnail_url")
        return data

    def create(self, validated_data):
        """
        Creates a Video instance and assigns the themes list.
        """
        has_pw_flag = self.initial_data.get("has_password")
        if str(has_pw_flag).lower() == "false":
            validated_data["password"] = ""

        themes_data = validated_data.pop("themes", None)
        video = super().create(validated_data)
        if themes_data is not None:
            for theme in themes_data:
                ThemeItem.objects.create(theme=theme, video=video)
        return video

    def update(self, instance, validated_data):
        """
        Updates a Video instance and updates its themes list.
        """
        has_pw_flag = self.initial_data.get("has_password")
        if str(has_pw_flag).lower() == "false":
            validated_data["password"] = ""

        themes_data = validated_data.pop("themes", None)
        video = super().update(instance, validated_data)
        if themes_data is not None:
            ThemeItem.objects.filter(video=video).delete()
            for theme in themes_data:
                ThemeItem.objects.create(theme=theme, video=video)
        return video
