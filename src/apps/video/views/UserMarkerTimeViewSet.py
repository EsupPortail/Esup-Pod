"""
Esup-Pod - UserMarkerTime viewset.
"""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from src.apps.video.conf import video_settings
from src.apps.video.models import Video, UserMarkerTime
from src.apps.video.serializers import UserMarkerTimeSerializer


class UserMarkerTimeViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user video playback marker (resume position).
    Only the authenticated user's own marker is accessible.
    """

    serializer_class = UserMarkerTimeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _check_feature_enabled(self):
        """Returns a 400 Response if the marker time feature is disabled, else None."""
        if not video_settings.use_marker_time:
            return Response(
                {"detail": _("Playback resume feature is disabled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return None

    def _get_video_or_404(self, video_slug):
        """Returns the Video instance or raises NotFound."""
        video = Video.objects.filter(slug=video_slug).first()
        if not video:
            raise NotFound(_("Video not found."))
        return video

    @extend_schema(
        summary="Get playback marker",
        responses={200: UserMarkerTimeSerializer},
    )
    @action(detail=False, methods=["get"], url_path=r"(?P<video_slug>[\w-]+)")
    def get_marker(self, request, video_slug=None):
        """
        GET /api/marker/{video_slug}/
        Returns the current playback position for the authenticated user. Returns 0 if no marker exists yet.
        """
        disabled = self._check_feature_enabled()
        if disabled:
            return disabled

        video = self._get_video_or_404(video_slug)

        marker_time = UserMarkerTime.objects.filter(
            video=video, user=request.user
        ).first()
        marker = marker_time.marker if marker_time else 0
        return Response({"marker": marker, "video": video_slug})

    @extend_schema(
        summary="Save playback marker",
        request={
            "application/json": {
                "type": "object",
                "properties": {"marker": {"type": "integer"}},
            }
        },
        responses={200: UserMarkerTimeSerializer},
    )
    @action(detail=False, methods=["post"], url_path=r"(?P<video_slug>[\w-]+)/save")
    def save_marker(self, request, video_slug=None):
        """
        POST /api/marker/{video_slug}/save/
        Saves or updates the playback position for the authenticated user.
        """
        disabled = self._check_feature_enabled()
        if disabled:
            return disabled

        video = self._get_video_or_404(video_slug)

        marker_value = request.data.get("marker", 0)
        marker_time, _created = UserMarkerTime.objects.update_or_create(
            video=video,
            user=request.user,
            defaults={"marker": marker_value},
        )
        return Response({"marker": marker_time.marker})

    @extend_schema(
        summary="Reset playback marker",
        responses={204: None},
    )
    @action(detail=False, methods=["delete"], url_path=r"(?P<video_slug>[\w-]+)/reset")
    def reset_marker(self, request, video_slug=None):
        """
        DELETE /api/marker/{video_slug}/reset/
        Resets (deletes) the marker for the authenticated user on this video.
        """
        disabled = self._check_feature_enabled()
        if disabled:
            return disabled

        video = self._get_video_or_404(video_slug)

        UserMarkerTime.objects.filter(video=video, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
