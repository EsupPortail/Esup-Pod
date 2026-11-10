"""
Esup-Pod - ViewSet for the Chapter model.
- Read: chapters of the videos visible to the current user, on the current site.
- Write/Delete: same rights as editing the linked video (owner, co-owners,
  channel collaborators, superusers).
"""

from django.contrib.sites.shortcuts import get_current_site
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import permissions, viewsets
from rest_framework.exceptions import PermissionDenied

from src.apps.video.models import Chapter, Video
from src.apps.video.permissions import IsOwnerOrCoOwnerOrChannelCollaborator
from src.apps.video.serializers import ChapterSerializer


class IsChapterVideoEditorOrReadOnly(permissions.BasePermission):
    """
    Esup-Pod - Read for everyone (the queryset is already filtered by
    visibility); write only for users who can edit the chapter's video.
    """

    def has_object_permission(self, request, view, obj):
        """Delegate the write check to the video permission."""
        return IsOwnerOrCoOwnerOrChannelCollaborator().has_object_permission(
            request, view, obj.video
        )


@extend_schema_view(
    list=extend_schema(
        summary="List chapters",
        description=(
            "List the chapters of the videos visible to the current user. "
            "When `video_id` or `video_slug` is provided, the result is not paginated."
        ),
        parameters=[
            OpenApiParameter(
                name="video_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Only chapters of this video ID.",
            ),
            OpenApiParameter(
                name="video_slug",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Only chapters of the video with this slug.",
            ),
        ],
    ),
    retrieve=extend_schema(summary="Retrieve a chapter"),
    create=extend_schema(
        summary="Create a chapter",
        description=(
            "Add a chapter to a video. `time_start` (in seconds) must be lower than "
            "the video duration and unique for this video."
        ),
    ),
    update=extend_schema(summary="Update a chapter"),
    partial_update=extend_schema(summary="Partially update a chapter"),
    destroy=extend_schema(summary="Delete a chapter"),
)
class ChapterViewSet(viewsets.ModelViewSet):
    """
    Esup-Pod - Provides CRUD operations for Chapter objects.
    Supports filtering by `video_id` or `video_slug` query parameters.
    """

    serializer_class = ChapterSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsChapterVideoEditorOrReadOnly,
    ]

    def get_queryset(self):
        """Return the chapters of the videos visible on the current site."""
        current_site = get_current_site(self.request)
        visible_videos = Video.objects.visible_for(self.request.user).filter(
            sites=current_site
        )
        queryset = Chapter.objects.filter(video__in=visible_videos).select_related(
            "video"
        )

        video_id = self.request.query_params.get("video_id")
        if video_id:
            if not video_id.isdigit():
                return queryset.none()
            queryset = queryset.filter(video_id=int(video_id))

        video_slug = self.request.query_params.get("video_slug")
        if video_slug:
            queryset = queryset.filter(video__slug=video_slug)
        return queryset

    def paginate_queryset(self, queryset):
        """Do not paginate when the list is already scoped to one video."""
        params = self.request.query_params
        if params.get("video_id") or params.get("video_slug"):
            return None
        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        """Check that the user can edit the target video before creating."""
        video = serializer.validated_data["video"]
        if not IsOwnerOrCoOwnerOrChannelCollaborator().has_object_permission(
            self.request, self, video
        ):
            raise PermissionDenied(
                "You do not have permission to manage chapters for this video."
            )
        serializer.save()
