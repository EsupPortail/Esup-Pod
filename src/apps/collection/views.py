"""
Esup-Pod - Viewsets for distinct collection models.
"""

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

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
from django_filters.rest_framework import DjangoFilterBackend
from src.apps.collection.filters import ChannelFilterSet, PlaylistFilterSet


@extend_schema_view(
    list=extend_schema(
        summary="List channels",
        description="Retrieve a list of video channels, filtered by user visibility (public channels, owned channels, or channels where the user is a collaborator). Supports multi-value filtering for owner username (e.g., `?owner__username=alice&owner__username=bob`).",
    ),
    retrieve=extend_schema(
        summary="Retrieve channel details",
        description="Retrieve details of a specific video channel by its slug.",
    ),
    create=extend_schema(
        summary="Create a channel",
        description="Create a new video channel. The authenticated user is automatically set as the owner.",
    ),
    update=extend_schema(
        summary="Update a channel",
        description="Fully update a channel's details. Only the channel owner or a collaborator can update it.",
    ),
    partial_update=extend_schema(
        summary="Partially update a channel",
        description="Partially update a channel's details. Only the channel owner or a collaborator can update it.",
    ),
    destroy=extend_schema(
        summary="Delete a channel",
        description="Permanently delete a channel. Only the channel owner or a collaborator can delete it.",
    ),
)
class ChannelViewSet(viewsets.ModelViewSet):
    """API view set for the Channel model."""

    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsChannelOwnerOrCollaboratorOrReadOnly,
    ]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "description", "owner__username"]
    ordering_fields = ["created_at", "title"]
    filterset_class = ChannelFilterSet

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


@extend_schema_view(
    list=extend_schema(
        summary="List top-level themes",
        description="Retrieve a list of all root/top-level themes (categories) for channels, filtered by visibility and user access permissions.",
        parameters=[
            OpenApiParameter(
                name="channel",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter themes associated with a specific Channel ID.",
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve theme details",
        description="Retrieve detailed information about a theme by its slug, including children/sub-themes.",
    ),
    create=extend_schema(
        summary="Create a theme",
        description="Create a new theme. Restricted to authenticated users/theme owners.",
    ),
    update=extend_schema(
        summary="Update a theme",
        description="Fully update a theme. Restricted to theme owners.",
    ),
    partial_update=extend_schema(
        summary="Partially update a theme",
        description="Partially update a theme. Restricted to theme owners.",
    ),
    destroy=extend_schema(
        summary="Delete a theme",
        description="Permanently delete a theme. Restricted to theme owners.",
    ),
)
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


@extend_schema_view(
    list=extend_schema(
        summary="List playlists",
        description="Retrieve a list of video playlists. For anonymous users, only public playlists are shown. Authenticated users see both public and owned playlists. Supports multi-value filtering for owner username (e.g., `?owner__username=alice&owner__username=bob`).",
    ),
    retrieve=extend_schema(
        summary="Retrieve playlist details",
        description="Retrieve details of a specific playlist by slug. Supports password verification via '?password' query param or 'X-Playlist-Password' header.",
    ),
    create=extend_schema(
        summary="Create a playlist",
        description="Create a new playlist. The authenticated user is set as the owner.",
    ),
    update=extend_schema(
        summary="Update a playlist",
        description="Fully update a playlist. Only the playlist owner can perform this action.",
    ),
    partial_update=extend_schema(
        summary="Partially update a playlist",
        description="Partially update a playlist. Only the playlist owner can perform this action.",
    ),
    destroy=extend_schema(
        summary="Delete a playlist",
        description="Permanently delete a playlist. Only the playlist owner can perform this action.",
    ),
)
class PlaylistViewSet(viewsets.ModelViewSet):
    """API view set for the Playlist model."""

    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "description", "owner__username"]
    ordering_fields = ["created_at", "title"]
    filterset_class = PlaylistFilterSet

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
                    from django.contrib.auth.hashers import check_password, make_password
                    import hashlib

                    if check_password(provided, instance.password):
                        context["password_verified"] = True
                    else:
                        hashed_provided = hashlib.sha256(
                            provided.encode("utf-8")
                        ).hexdigest()
                        if hashed_provided == instance.password:
                            context["password_verified"] = True
                            # Upgrade the password to the Django standard hash format on successful verification
                            instance.password = make_password(provided)
                            instance.save(update_fields=["password"])
        return context

    def perform_create(self, serializer):
        """Set the current user as owner upon playlist creation."""
        serializer.save(owner=self.request.user)

    @extend_schema(
        summary="Add video to playlist",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "integer",
                        "description": "ID of the video to add.",
                    }
                },
                "required": ["video_id"],
            }
        },
        responses={
            201: OpenApiResponse(
                description="Video added successfully.",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "video added"}
                    },
                },
            ),
            400: OpenApiResponse(description="Video already in playlist."),
        },
    )
    @action(detail=True, methods=["post"])
    def add_video(self, request, slug=None):
        """
        Adds a video (by its ID) to the playlist in a thread-safe and duplicate-protected manner.
        """
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

    @extend_schema(
        summary="Remove video from playlist",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "integer",
                        "description": "ID of the video to remove.",
                    }
                },
                "required": ["video_id"],
            }
        },
        responses={
            204: OpenApiResponse(description="Video removed successfully."),
            404: OpenApiResponse(description="Video not found in playlist."),
        },
    )
    @action(detail=True, methods=["post"])
    def remove_video(self, request, slug=None):
        """Removes a video (by its ID) from the playlist."""
        playlist = self.get_object()
        video_id = request.data.get("video_id")
        item = get_object_or_404(PlaylistItem, playlist=playlist, video_id=video_id)
        item.delete()
        return Response({"status": "video removed"}, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Reorder playlist videos",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "positions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "video_id": {"type": "integer"},
                                "position": {"type": "integer"},
                            },
                            "required": ["video_id", "position"],
                        },
                    }
                },
                "required": ["positions"],
            }
        },
        responses={
            200: OpenApiResponse(
                description="Playlist reordered successfully.",
                response={
                    "type": "object",
                    "properties": {"status": {"type": "string", "example": "reordered"}},
                },
            )
        },
    )
    @action(detail=True, methods=["post"])
    def reorder(self, request, slug=None):
        """Reorder videos in the playlist by providing an array of objects mapping video IDs to their new positions."""
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


@extend_schema_view(
    list=extend_schema(
        summary="List user favorites",
        description="Retrieve a list of video favorites belonging to the currently authenticated user.",
    ),
    retrieve=extend_schema(
        summary="Retrieve a favorite item",
        description="Retrieve details of a specific favorite item by its ID. Restricted to the owner.",
    ),
    create=extend_schema(
        summary="Add video to favorites",
        description="Add a video to the user's favorites list. The authenticated user is automatically set as the owner.",
    ),
    update=extend_schema(
        summary="Update a favorite item",
        description="Fully update a favorite item. Restricted to the owner.",
    ),
    partial_update=extend_schema(
        summary="Partially update a favorite item",
        description="Partially update a favorite item. Restricted to the owner.",
    ),
    destroy=extend_schema(
        summary="Remove video from favorites",
        description="Remove a video from the user's favorites list by deleting the favorite item.",
    ),
)
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
