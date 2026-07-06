"""
Esup-Pod - ExternalRecording viewset.
"""

import logging

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from src.apps.import_video.conf import import_video_settings
from src.apps.import_video.models import ExternalRecording
from src.apps.import_video.permissions import CanImportVideo
from src.apps.import_video.serializers import ExternalRecordingSerializer
from src.apps.import_video.tasks import task_import_external_recording

logger = logging.getLogger(__name__)


class ExternalRecordingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing external video recordings.
    Supports listing, creating, retrieving, updating, and deleting recordings.
    Import to Pod is triggered via the import_to_pod action.
    """

    serializer_class = ExternalRecordingSerializer
    permission_classes = [permissions.IsAuthenticated, CanImportVideo]
    lookup_field = "id"

    def get_queryset(self):
        """Returns recordings filtered by the current site and owner."""
        from django.contrib.sites.shortcuts import get_current_site

        current_site = get_current_site(self.request)
        qs = ExternalRecording.objects.filter(site=current_site)

        if not self.request.user.is_superuser:
            qs = qs.filter(owner=self.request.user)

        return qs

    def perform_create(self, serializer):
        """Creates a new recording, assigning the current user and site."""
        from django.contrib.sites.shortcuts import get_current_site

        if import_video_settings.restrict_to_staff:
            has_role = (
                hasattr(self.request.user, "owner")
                and self.request.user.owner.server_roles.filter(
                    can_import_video=True
                ).exists()
            )
            if (
                not self.request.user.is_staff
                and not self.request.user.is_superuser
                and not has_role
            ):
                raise PermissionDenied(
                    _(
                        "Only staff members or users with import roles are allowed to create external recordings."
                    )
                )

        current_site = get_current_site(self.request)
        serializer.save(owner=self.request.user, site=current_site)

    def perform_update(self, serializer):
        """Updates a recording, restricted to owner or superuser."""
        recording = self.get_object()
        if recording.owner != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied(
                _("You do not have permission to update this recording.")
            )
        serializer.save()

    def perform_destroy(self, instance):
        """Deletes a recording, restricted to owner or superuser."""
        if instance.owner != self.request.user and not self.request.user.is_superuser:
            raise PermissionDenied(
                _("You do not have permission to delete this recording.")
            )
        instance.delete()

    @extend_schema(
        summary=_("Import recording to Pod"),
        request=None,
        responses={
            202: {"type": "object", "properties": {"status": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
    )
    @action(detail=True, methods=["post"], url_path="import")
    def import_to_pod(self, request, id=None):
        """
        Triggers an asynchronous import of the external recording into Pod.
        Returns 202 Accepted immediately.
        Track progress via the import_status field.
        """
        recording = self.get_object()

        if recording.import_status == ExternalRecording.ImportStatus.PROCESSING:
            return Response(
                {"detail": _("Import already in progress.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if recording.import_status == ExternalRecording.ImportStatus.DONE:
            return Response(
                {"detail": _("Recording already imported.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recording.import_status = ExternalRecording.ImportStatus.PROCESSING
        recording.save(update_fields=["import_status"])

        task_import_external_recording.delay(recording.id, request.user.id)

        logger.info(
            "Import task queued for recording %s by user %s",
            recording.id,
            request.user.username,
        )

        return Response(
            {"status": "queued"},
            status=status.HTTP_202_ACCEPTED,
        )

    @extend_schema(
        summary=_("Reset import status"),
        request=None,
        responses={
            200: {"type": "object", "properties": {"status": {"type": "string"}}},
        },
    )
    @action(detail=True, methods=["post"], url_path="reset")
    def reset_import(self, request, id=None):
        """
        Resets the import status to PENDING, allowing a new import attempt.
        """
        recording = self.get_object()

        if recording.import_status == ExternalRecording.ImportStatus.PROCESSING:
            return Response(
                {"detail": _("Cannot reset an import that is currently processing.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recording.import_status = ExternalRecording.ImportStatus.PENDING
        recording.error_message = ""
        recording.imported_at = None
        recording.save(update_fields=["import_status", "error_message", "imported_at"])

        return Response({"status": "reset"}, status=status.HTTP_200_OK)
