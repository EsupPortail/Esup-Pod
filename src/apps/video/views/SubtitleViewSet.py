"""
Esup-Pod - Subtitle viewset.
"""

from rest_framework import viewsets, permissions, parsers
from rest_framework.exceptions import PermissionDenied
from django.contrib.sites.shortcuts import get_current_site
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from src.apps.video.models import Subtitle
from src.apps.video.serializers import SubtitleSerializer


class IsSubtitleVideoOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Read: Allowed for everyone (or based on global config).
    - Write/Delete: Allowed only if the user is the owner of the linked video.
    """

    def has_object_permission(self, request, view, obj):
        """Check if the requesting user is the owner of the video linked to the subtitle."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.video.owner == request.user


@extend_schema_view(
    list=extend_schema(
        summary="List all subtitles",
        description="Retrieve a list of video subtitles, isolated by the current site domain.",
        parameters=[
            OpenApiParameter(
                name="video_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter subtitles associated with a specific Video ID.",
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Retrieve a subtitle track",
        description="Retrieve details of a specific subtitle track.",
    ),
    create=extend_schema(
        summary="Upload a subtitle track",
        description="Add a new subtitle file (.vtt or .srt) to a video. Only the video owner or a superuser is allowed to upload subtitles for a video.",
    ),
    update=extend_schema(
        summary="Update a subtitle track",
        description="Fully update an existing subtitle track. Only the video owner is allowed to perform this action.",
    ),
    partial_update=extend_schema(
        summary="Partially update a subtitle track",
        description="Partially update an existing subtitle track. Only the video owner is allowed to perform this action.",
    ),
    destroy=extend_schema(
        summary="Delete a subtitle track",
        description="Permanently delete a subtitle track and its file from the system. Only the video owner is allowed to delete it.",
    ),
)
class SubtitleViewSet(viewsets.ModelViewSet):
    """
    API endpoint to handle subtitles (upload, listing, deletion).
    """

    queryset = Subtitle.objects.all()
    serializer_class = SubtitleSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsSubtitleVideoOwnerOrReadOnly,
    ]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        """
        Allows filtering subtitles by video, while ensuring isolation by current site.
        """
        current_site = get_current_site(self.request)
        queryset = Subtitle.objects.filter(video__sites=current_site)

        video_id = self.request.query_params.get("video_id")
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        return queryset.distinct()

    def perform_create(self, serializer):
        """
        Security check at creation time.
        """
        video = serializer.validated_data.get("video")
        if (
            video
            and video.owner != self.request.user
            and not self.request.user.is_superuser
        ):
            raise PermissionDenied(
                "You cannot add subtitles to a video that does not belong to you."
            )
        serializer.save()
