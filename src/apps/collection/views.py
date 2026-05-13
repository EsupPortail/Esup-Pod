"""
Esup-Pod - Viewsets for distinct collection models.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from src.apps.collection.models import (
    Channel,
    Theme,
    Playlist,
    PlaylistItem,
    Favorite,
)
from src.apps.collection.serializers import (
    ChannelSerializer,
    ThemeSerializer,
    PlaylistSerializer,
    FavoriteSerializer,
)
from src.apps.collection.permissions import (
    IsOwnerOrReadOnly,
    IsChannelOwnerOrCollaboratorOrReadOnly,
    IsAdminOrThemeOwner,
)
from src.apps.video.models import Video


class ChannelViewSet(viewsets.ModelViewSet):
    """API view set for the Channel model."""

    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsChannelOwnerOrCollaboratorOrReadOnly,
    ]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "owner__username"]
    ordering_fields = ["created_at", "title"]

    def get_queryset(self):
        """Return channels filtered by user visibility (public, owned, or collaborated)."""
        user = self.request.user
        qs = (
            super()
            .get_queryset()
            .select_related("owner")
            .prefetch_related("collaborators")
        )
        if not user.is_authenticated:
            return qs.filter(is_public=True)
        if user.is_superuser:
            return qs
        return qs.filter(
            Q(is_public=True) | Q(owner=user) | Q(collaborators=user)
        ).distinct()

    def perform_create(self, serializer):
        """Set the current user as owner upon channel creation."""
        serializer.save(owner=self.request.user)


class ThemeViewSet(viewsets.ModelViewSet):
    """API view set for the Theme model."""

    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrThemeOwner]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description"]

    def get_queryset(self):
        """Return themes filtered by channel, visibility, and user access rights."""
        qs = Theme.objects.all().prefetch_related("children", "themeitem_set__video")
        channel_id = self.request.query_params.get("channel")
        if channel_id:
            qs = qs.filter(channel_id=channel_id)

        user = self.request.user
        if not user.is_authenticated:
            qs = qs.filter(Q(channel__isnull=True) | Q(channel__is_public=True))
        elif not user.is_superuser:
            qs = qs.filter(
                Q(channel__isnull=True)
                | Q(channel__is_public=True)
                | Q(channel__owner=user)
                | Q(channel__collaborators=user)
            ).distinct()

        if self.action == "list":
            return qs.filter(parent__isnull=True)
        return qs


class PlaylistViewSet(viewsets.ModelViewSet):
    """API view set for the Playlist model."""

    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        """Return playlists filtered by user visibility (public or owned)."""
        user = self.request.user
        qs = (
            super()
            .get_queryset()
            .select_related("owner")
            .prefetch_related("items__video")
        )
        if not user.is_authenticated:
            return qs.filter(is_public=True)
        if user.is_superuser:
            return qs
        return qs.filter(Q(is_public=True) | Q(owner=user))

    def get_serializer_context(self):
        """Inject password_verified flag into context for protected playlists."""
        context = super().get_serializer_context()
        if self.action == "retrieve":
            instance = self.get_object()
            if getattr(instance, "password", None):
                provided = self.request.query_params.get(
                    "password"
                ) or self.request.headers.get("X-Playlist-Password")
                if provided:
                    from django.contrib.auth.hashers import check_password

                    if check_password(provided, instance.password):
                        context["password_verified"] = True
        return context

    def perform_create(self, serializer):
        """Set the current user as owner upon playlist creation."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def add_video(self, request, slug=None):
        """Add a video to the playlist in a thread-safe manner."""
        from django.db import transaction

        video_id = request.data.get("video_id")
        video = get_object_or_404(Video, pk=video_id)

        with transaction.atomic():
            playlist = Playlist.objects.select_for_update().get(slug=slug)

            if PlaylistItem.objects.filter(playlist=playlist, video=video).exists():
                return Response(
                    {"error": "Video already in playlist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            PlaylistItem.objects.create(playlist=playlist, video=video)
        return Response({"status": "video added"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def remove_video(self, request, slug=None):
        """Remove a video from the playlist."""
        playlist = self.get_object()
        video_id = request.data.get("video_id")
        item = get_object_or_404(PlaylistItem, playlist=playlist, video_id=video_id)
        item.delete()
        return Response({"status": "video removed"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def reorder(self, request, slug=None):
        """Reorder videos in the playlist by updating their position values."""
        playlist = self.get_object()
        positions = request.data.get("positions", [])
        updated_items = []
        for pos_data in positions:
            video_id = pos_data.get("video_id")
            new_pos = pos_data.get("position")
            item = playlist.items.filter(video_id=video_id).first()
            if item:
                item.position = new_pos
                updated_items.append(item)
        PlaylistItem.objects.bulk_update(updated_items, ["position"])
        return Response({"status": "reordered"}, status=status.HTTP_200_OK)


class FavoriteViewSet(viewsets.ModelViewSet):
    """API view set for the Favorite model."""

    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the favorites belonging to the current user."""
        return Favorite.objects.select_related("user", "video").filter(
            user=self.request.user
        )

    def perform_create(self, serializer):
        """Set the current user upon favorite creation."""
        serializer.save(user=self.request.user)
