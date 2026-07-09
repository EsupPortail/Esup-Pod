"""
Esup-Pod - VideoCut viewset.
"""

from rest_framework import viewsets, status
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from src.apps.video.models import Video
from src.apps.video.serializers import VideoCutSerializer
from src.apps.video.conf import video_settings
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema


class VideoCutViewSet(CreateModelMixin, DestroyModelMixin, viewsets.GenericViewSet):
    """ViewSet for video cut management.
    Supports creation (POST) and deletion (DELETE) of a video cut.
    Permissions are checked via a private helper method.
    """

    @extend_schema(
        summary=_("Create or replace a video cut"),
        request=VideoCutSerializer,
        responses={
            201: VideoCutSerializer,
            400: "Bad request",
            403: "Forbidden",
            404: "Not found",
        },
    )
    def create(self, request, video_slug=None):
        """
        Creates or replaces a cut for the given video. time_start and time_end are in seconds.

        The method validates permissions, validates the payload, removes any existing cut,
        deletes time‑dependent objects (chapters, notes) and then creates the new cut.
        """
        # 0️⃣ Check configuration
        if not video_settings.use_cut:
            return Response(
                {"detail": _("The video cutting feature is disabled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1️⃣ Retrieve video
        try:
            video = Video.objects.get(slug=video_slug)
        except Video.DoesNotExist:
            raise NotFound(_("Video not found."))

        # 2️⃣ Permission check (shared logic)
        self._assert_edit_permission(request, video)

        # 3️⃣ Validate payload
        serializer = VideoCutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 4️⃣ Replace existing cut (one‑to‑one relationship)
        if hasattr(video, "cut") and video.cut:
            video.cut.delete()
        video_cut = serializer.save(video=video)

        # 5️⃣ Clean time‑dependent data
        if hasattr(video, "chapters"):
            video.chapters.all().delete()
        if hasattr(video, "notes"):
            video.notes.all().delete()

        return Response(
            VideoCutSerializer(video_cut).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary=_("Delete a video cut"),
        responses={
            204: None,
            403: "Forbidden",
            404: "Not found",
        },
    )
    def destroy(self, request, video_slug=None):
        """Deletes the cut associated with the given video."""
        # Check configuration
        if not video_settings.use_cut:
            return Response(
                {"detail": _("The video cutting feature is disabled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Retrieve video
        try:
            video = Video.objects.get(slug=video_slug)
        except Video.DoesNotExist:
            raise NotFound(_("Video not found."))

        # Permission check
        self._assert_edit_permission(request, video)

        # Delete the cut; raise 404 if none exists
        if not hasattr(video, "cut") or video.cut is None:
            raise NotFound(_("No cut found for this video."))
        video.cut.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _assert_edit_permission(self, request, video):
        """Internal helper to enforce edit permissions.

        Allows owners, co‑owners, super‑users, and optionally staff members if
        `video_settings.restrict_edit_to_staff` is enabled.
        """
        is_owner = video.owner == request.user
        is_co_owner = video.co_owners.filter(pk=request.user.pk).exists()
        if not (is_owner or is_co_owner or request.user.is_superuser):
            raise PermissionDenied(
                _("You do not have permission to modify this video cut.")
            )
        if video_settings.restrict_edit_to_staff and not request.user.is_staff:
            raise PermissionDenied(
                _("Only staff members are allowed to modify video cuts.")
            )
