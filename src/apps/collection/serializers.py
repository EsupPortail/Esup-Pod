"""
Esup-Pod - Serializers for the distinct collection models.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.contrib.auth import get_user_model
from src.apps.collection.models import (
    Channel,
    Theme,
    ThemeItem,
    Playlist,
    PlaylistItem,
    Favorite,
)
from src.apps.video.serializers import VideoSerializer

User = get_user_model()


class ChannelSerializer(serializers.ModelSerializer):
    """Serializer for the Channel model."""

    owner_username = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        """ChannelSerializer metadata."""

        model = Channel
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "owner",
            "owner_username",
            "is_public",
            "logo",
            "banner",
            "collaborators",
            "old_v4_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "owner", "created_at", "updated_at"]
        extra_kwargs = {
            "is_public": {"required": False},
        }


class ThemeItemSerializer(serializers.ModelSerializer):
    """Serializer for videos within a Theme."""

    video = VideoSerializer(read_only=True)

    class Meta:
        """ThemeItemSerializer metadata."""

        model = ThemeItem
        fields = ["id", "video", "added_at"]


class ThemeSerializer(serializers.ModelSerializer):
    """Recursive serializer for the Theme model."""

    children = serializers.SerializerMethodField()
    items = serializers.SerializerMethodField()

    class Meta:
        """ThemeSerializer metadata."""

        model = Theme
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "parent",
            "channel",
            "old_v4_id",
            "created_at",
            "updated_at",
            "children",
            "items",
        ]
        read_only_fields = ["slug", "created_at", "updated_at"]

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_children(self, obj):
        """Recursively serialize children themes."""
        children = obj.children.all()
        if children:
            return ThemeSerializer(children, many=True, context=self.context).data
        return []

    @extend_schema_field(ThemeItemSerializer(many=True))
    def get_items(self, obj):
        """Return theme items, filtering out restricted videos."""
        request = self.context.get("request")
        user = request.user if request and request.user else None

        # We need a user object for visible_for, even if anonymous
        from django.contrib.auth.models import AnonymousUser

        search_user = user or AnonymousUser()
        from src.apps.video.models import Video

        visible_videos = Video.objects.visible_for(search_user)
        items = obj.themeitem_set.filter(video__in=visible_videos)
        return ThemeItemSerializer(items, many=True, context=self.context).data


class PlaylistItemSerializer(serializers.ModelSerializer):
    """Serializer for videos within a Playlist."""

    video = VideoSerializer(read_only=True)

    class Meta:
        """PlaylistItemSerializer metadata."""

        model = PlaylistItem
        fields = ["id", "video", "position", "added_at"]


class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for the Playlist model."""

    owner_username = serializers.ReadOnlyField(source="owner.username")
    items = serializers.SerializerMethodField()
    is_protected = serializers.SerializerMethodField()

    class Meta:
        """PlaylistSerializer metadata."""

        model = Playlist
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "owner",
            "owner_username",
            "is_public",
            "password",
            "is_protected",
            "old_v4_id",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = ["slug", "owner", "created_at", "updated_at"]
        extra_kwargs = {
            "password": {"write_only": True},
        }

    @extend_schema_field(serializers.BooleanField())
    def get_is_protected(self, obj):
        """Return True if the playlist has a password set."""
        return bool(obj.password)

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_items(self, obj):
        """Return playlist items, hiding them if protected and not unlocked."""
        request = self.context.get("request")
        if obj.password:
            is_owner = (
                request and request.user.is_authenticated and request.user == obj.owner
            )
            is_verified = self.context.get("password_verified", False)
            if not (is_owner or is_verified):
                return []

        user = request.user if request and request.user else None
        from django.contrib.auth.models import AnonymousUser

        search_user = user or AnonymousUser()
        from src.apps.video.models import Video

        visible_videos = Video.objects.visible_for(search_user)
        items = obj.items.filter(video__in=visible_videos)
        return PlaylistItemSerializer(items, many=True, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer for the Favorite model."""

    user_username = serializers.ReadOnlyField(source="user.username")
    video_details = VideoSerializer(source="video", read_only=True)

    class Meta:
        """FavoriteSerializer metadata."""

        model = Favorite
        fields = ["id", "user", "user_username", "video", "video_details", "added_at"]
        read_only_fields = ["user", "added_at"]
