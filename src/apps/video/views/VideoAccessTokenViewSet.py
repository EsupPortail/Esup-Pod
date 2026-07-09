"""
Esup-Pod - VideoAccessToken viewset.
"""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from src.apps.video.conf import video_settings
from src.apps.video.models import VideoAccessToken
from src.apps.video.serializers import VideoAccessTokenSerializer


class VideoAccessTokenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing video access tokens.

    Owners and co-owners can create/list/revoke tokens for their videos.
    Anyone (including unauthenticated users) can validate a token via /resolve/.
    """

    serializer_class = VideoAccessTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Returns only tokens created by the current user."""
        return VideoAccessToken.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """Assigns the creator and validates ownership of the target video."""
        if not video_settings.use_video_access_token:
            raise PermissionDenied(_("Video access token feature is disabled."))

        video = serializer.validated_data.get("video")
        user = self.request.user

        is_owner = video.owner == user
        is_co_owner = video.co_owners.filter(pk=user.pk).exists()
        if not is_owner and not is_co_owner and not user.is_superuser:
            raise PermissionDenied(_("You can only create tokens for videos you own."))
        serializer.save(created_by=user)

    @extend_schema(
        summary="Resolve an access token",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "video_slug": {"type": "string"},
                    "video_title": {"type": "string"},
                    "expires_at": {"type": "string", "format": "date-time"},
                },
            },
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path=r"resolve/(?P<token>[0-9a-f-]+)",
        permission_classes=[permissions.AllowAny],
    )
    def resolve(self, request, token=None):
        """
        GET /api/tokens/resolve/{token}/
        Public endpoint — validates a token and returns video access info.
        """
        try:
            access_token = VideoAccessToken.objects.select_related("video").get(
                token=token
            )
        except VideoAccessToken.DoesNotExist:
            return Response({"detail": _("Invalid token.")}, status=404)

        if not access_token.is_valid():
            return Response(
                {"detail": _("This token has expired or been revoked.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        access_token.record_use()

        return Response(
            {
                "video_slug": access_token.video.slug,
                "video_title": access_token.video.title,
                "expires_at": access_token.expires_at,
            }
        )

    @extend_schema(
        summary="Revoke an access token",
        request=None,
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        """
        POST /api/tokens/{id}/revoke/
        Revokes (deactivates) a token without deleting it.
        """
        token = self.get_object()
        token.is_active = False
        token.save(update_fields=["is_active"])
        return Response({"status": "revoked"})
