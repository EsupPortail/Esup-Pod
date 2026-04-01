"""
Esup-Pod - Subtitle viewset.
"""

from rest_framework import viewsets, permissions, parsers
from rest_framework.exceptions import PermissionDenied
from django.contrib.sites.shortcuts import get_current_site
from src.apps.video.models import Subtitle
from src.apps.video.serializers import SubtitleSerializer


class IsSubtitleVideoOwnerOrReadOnly(permissions.BasePermission):
    """
    Esup-Pod - Custom permission:
    - Read: Allowed for everyone (or based on global config).
    - Write/Delete: Allowed only if the user is the owner of the linked video.
    """

    def has_object_permission(self, request, view, obj):
        """Check if the requesting user is the owner of the video linked to the subtitle."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.video.owner == request.user


class SubtitleViewSet(viewsets.ModelViewSet):
    """
    Esup-Pod - API endpoint to handle subtitles (upload, listing, deletion).
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
