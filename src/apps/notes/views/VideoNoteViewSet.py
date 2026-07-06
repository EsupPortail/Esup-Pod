"""
Esup-Pod - VideoNote viewset.
"""

import logging

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError

from src.apps.notes.conf import notes_settings
from src.apps.notes.models import VideoNote
from src.apps.notes.permissions import IsNoteOwner
from src.apps.notes.serializers import VideoNoteSerializer

logger = logging.getLogger(__name__)


class VideoNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing video notes.

    Notes are filtered by video slug and privacy status.
    Only the owner can update or delete their notes.
    """

    serializer_class = VideoNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsNoteOwner]

    def initial(self, request, *args, **kwargs):
        """Checks if the notes feature is enabled before processing."""
        super().initial(request, *args, **kwargs)
        if not notes_settings.use_notes:
            raise ValidationError({"detail": _("Notes feature is disabled.")})

    def get_queryset(self):
        """
        Returns notes filtered by video slug and privacy.
        Public notes and the user's own notes are returned.
        """
        user = self.request.user
        qs = VideoNote.objects.select_related("video", "owner")

        video_slug = self.request.query_params.get("video")
        if video_slug:
            qs = qs.filter(video__slug=video_slug)

        qs = qs.filter(Q(privacy=VideoNote.PrivacyStatus.PUBLIC) | Q(owner=user))

        return qs.distinct()

    def perform_create(self, serializer):
        """Creates a note, assigning the current user as owner."""
        video = serializer.validated_data.get("video")

        from src.apps.video.models import Video
        from django.contrib.sites.shortcuts import get_current_site

        current_site = get_current_site(self.request)
        if (
            not Video.objects.visible_for(self.request.user)
            .filter(id=video.id, sites=current_site)
            .exists()
        ):
            raise PermissionDenied(_("You do not have access to this video."))

        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """Updates a note, restricted to the owner."""
        if serializer.instance.owner != self.request.user:
            raise PermissionDenied(_("You can only edit your own notes."))
        serializer.save()

    def perform_destroy(self, instance):
        """Deletes a note, restricted to the owner."""
        if instance.owner != self.request.user:
            raise PermissionDenied(_("You can only delete your own notes."))
        instance.delete()

    @extend_schema(
        summary="List video notes",
        parameters=[
            OpenApiParameter(
                name="video",
                description="Video slug to filter notes by.",
                required=False,
                type=str,
            )
        ],
        responses={200: VideoNoteSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        """
        Returns notes for a given video slug.
        Public notes and the current user's own notes are returned.
        Filter by ?video=<slug>.
        """
        return super().list(request, *args, **kwargs)
