"""
Esup-Pod - BroadcasterViewSet.
"""

import logging

from rest_framework import viewsets, mixins, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.utils.translation import gettext_lazy as _

from src.apps.live.models import Broadcaster
from src.apps.live.serializers import BroadcasterSerializer
from src.apps.live.permissions import CanPilotBroadcaster
from src.apps.live.conf import live_settings

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List broadcasters",
        description="Returns all public broadcasters for the current site. Filter by building with `?building={id}`.",
    ),
    retrieve=extend_schema(
        summary="Get broadcaster",
        description="Returns details of a broadcaster. Restricted broadcasters require authentication.",
    ),
)
class BroadcasterViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for Broadcaster.

    GET  /api/live/broadcasters/                          — List public broadcasters.
    GET  /api/live/broadcasters/{slug}/                   — Broadcaster detail.
    PATCH /api/live/broadcasters/{slug}/                  — Update status (triggers transcription).
    GET  /api/live/broadcasters/from_building/            — Broadcasters of a given building.
    GET  /api/live/broadcasters/{slug}/restriction/       — Check if broadcaster is restricted.
    GET  /api/live/broadcasters/{slug}/available/         — Is available AND recording status.
    POST /api/live/broadcasters/{slug}/start_record/      — Start recording (piloting).
    POST /api/live/broadcasters/{slug}/stop_record/       — Stop recording (piloting).
    POST /api/live/broadcasters/{slug}/split_record/      — Split recording (Wowza only).
    POST /api/live/broadcasters/{slug}/start_stream/      — Start RTMP stream (SMP only).
    POST /api/live/broadcasters/{slug}/stop_stream/       — Stop RTMP stream (SMP only).
    GET  /api/live/broadcasters/{slug}/record_status/     — Is currently recording?
    GET  /api/live/broadcasters/{slug}/record_info/       — Current recording info (duration, file).
    """

    serializer_class = BroadcasterSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name", "description"]
    filterset_fields = ["building", "public", "is_restricted"]

    def get_queryset(self):
        """Return broadcasters visible on the current site."""
        site = get_current_site(self.request)
        qs = Broadcaster.objects.filter(building__sites=site).select_related("building")
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(public=True)
        return qs.order_by("building", "name")

    def get_permissions(self):
        """Apply CanPilotBroadcaster only for piloting actions."""
        if self.action in (
            "start_record",
            "stop_record",
            "split_record",
            "start_stream",
            "stop_stream",
        ):
            return [permissions.IsAuthenticated(), CanPilotBroadcaster()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """
        Return broadcaster details.
        Restricted broadcasters require authentication.
        """
        broadcaster = self.get_object()
        if broadcaster.is_restricted and not request.user.is_authenticated:
            return Response(
                {"detail": _("Authentication required to access this stream.")},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(broadcaster)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """Handle status updates and trigger live transcription if needed (V4 behaviour)."""
        response = super().partial_update(request, *args, **kwargs)

        if live_settings.use_live_transcription and response.status_code == 200:
            broadcaster = self.get_object()
            from src.apps.live.models import Event

            events = Event.objects.filter(
                broadcaster=broadcaster, enable_transcription=True
            )
            if events.exists():
                from src.apps.live.services.transcription import transcribe_live

                status_val = request.data.get("status")
                transcribe_live(
                    broadcaster.url,
                    broadcaster.slug,
                    status_val,
                    broadcaster.main_lang,
                    broadcaster.transcription_file.path,
                )
        return response

    # -------------------------------------------------------------------------
    # V4 helper endpoints
    # -------------------------------------------------------------------------

    @extend_schema(
        summary="Broadcasters from building",
        description="Return all public broadcasters for a given building (identified by name). "
        "Pass `?building=<name>` as query param.",
        responses={200: BroadcasterSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="from_building")
    def from_building(self, request):
        """GET /api/live/broadcasters/from_building/?building=<name>"""
        building_name = request.query_params.get("building")
        if not building_name:
            return Response(
                {"detail": _("'building' query parameter is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from src.apps.live.models import Building

        building = Building.objects.filter(name=building_name).first()
        if not building:
            return Response(
                {"detail": _("Building not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        # Mirror V4's get_available_broadcasters_of_building():
        # Keep broadcasters where enable_add_event=True AND (no manage_groups OR user is in manage_groups)
        qs = Broadcaster.objects.filter(building=building, enable_add_event=True)

        if user.is_authenticated:
            if not user.is_superuser:
                # Only return broadcasters the user can manage (no restriction OR user's groups match)
                qs = qs.filter(
                    models.Q(manage_groups__isnull=True)
                    | models.Q(manage_groups__in=user.groups.all())
                ).distinct()
        else:
            # Unauthenticated users get no results (event management requires auth)
            qs = qs.none()

        response_data = {}
        for broadcaster in qs:
            response_data[broadcaster.id] = {
                "id": broadcaster.id,
                "name": broadcaster.name,
                "restricted": broadcaster.is_restricted,
            }
        return Response(response_data)

    @extend_schema(
        summary="Broadcaster restriction status",
        description="Check if this broadcaster's access is restricted.",
        responses={
            200: {"type": "object", "properties": {"restricted": {"type": "boolean"}}}
        },
    )
    @action(detail=True, methods=["get"], url_path="restriction")
    def restriction(self, request, slug=None):
        """GET /api/live/broadcasters/{slug}/restriction/"""
        broadcaster = self.get_object()
        return Response({"restricted": broadcaster.is_restricted})

    @extend_schema(
        summary="Is available to record",
        description=(
            "Check if the broadcaster is available to start a new recording AND "
            "whether it is currently recording. Mirrors the V4 `ajax_is_stream_available_to_record`."
        ),
        responses={
            200: {
                "type": "object",
                "properties": {
                    "available": {"type": "boolean"},
                    "recording": {"type": "boolean"},
                },
            }
        },
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="available",
        permission_classes=[permissions.IsAuthenticated],
    )
    def available(self, request, slug=None):
        """GET /api/live/broadcasters/{slug}/available/"""
        broadcaster = self.get_object()
        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return Response(
                {
                    "available": False,
                    "recording": False,
                    "message": "implementation error",
                }
            )
        if impl.is_recording(with_file_check=True):
            return Response({"available": True, "recording": True})
        available = impl.is_available_to_record()
        return Response({"available": available, "recording": False})

    @extend_schema(
        summary="Current record info",
        description="Return metadata about the current recording (filename, duration in seconds, segment number).",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "duration": {"type": "integer"},
                    "currentFile": {"type": "string"},
                    "segmentNumber": {"type": "string"},
                },
            }
        },
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="record_info",
        permission_classes=[permissions.IsAuthenticated],
    )
    def record_info(self, request, slug=None):
        """GET /api/live/broadcasters/{slug}/record_info/"""
        broadcaster = self.get_object()
        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return Response({"success": False, "error": "implementation error"})

        info = impl.get_info_current_record()
        if info.get("durationInSeconds") != "":
            return Response(
                {
                    "success": True,
                    "duration": int(info.get("durationInSeconds", 0)),
                    "currentFile": info.get("currentFile", ""),
                    "segmentNumber": info.get("segmentNumber", ""),
                }
            )
        return Response({"success": False, "error": "No active recording info"})

    # -------------------------------------------------------------------------
    # Piloting endpoints
    # -------------------------------------------------------------------------

    def _get_piloting_or_error(self, broadcaster):
        """Return (impl, None) or (None, Response) if piloting is unavailable."""
        from src.apps.live.services.piloting import get_piloting_implementation

        impl = get_piloting_implementation(broadcaster)
        if impl is None:
            return None, Response(
                {
                    "detail": _(
                        "No piloting implementation configured for this broadcaster."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return impl, None

    @extend_schema(
        summary="Start recording",
        description="Start the recording on the broadcaster (requires piloting rights). Provide `event_id` in the request body.",
        responses={
            200: {"type": "object", "properties": {"success": {"type": "boolean"}}}
        },
    )
    @action(detail=True, methods=["post"], url_path="start_record")
    def start_record(self, request, slug=None):
        """POST /api/live/broadcasters/{slug}/start_record/"""
        broadcaster = self.get_object()
        self.check_object_permissions(request, broadcaster)
        event_id = request.data.get("event_id")
        if not event_id:
            return Response(
                {"detail": _("'event_id' is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return err
        if impl.is_recording():
            return Response(
                {"success": False, "detail": _("The broadcaster is already recording.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        success = impl.start_recording(int(event_id))
        if success:
            # Reset the is_recording_stopped flag on the event (matches V4 behaviour)
            from src.apps.live.models import Event

            Event.objects.filter(pk=event_id).update(is_recording_stopped=False)
        return Response({"success": success}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Stop recording",
        description="Stop the current recording. Creates the video via Celery after stopping.",
        responses={
            200: {"type": "object", "properties": {"success": {"type": "boolean"}}}
        },
    )
    @action(detail=True, methods=["post"], url_path="stop_record")
    def stop_record(self, request, slug=None):
        """POST /api/live/broadcasters/{slug}/stop_record/"""
        broadcaster = self.get_object()
        self.check_object_permissions(request, broadcaster)
        event_id = request.data.get("event_id")

        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return err

        if not impl.is_recording(with_file_check=True):
            return Response(
                {"success": False, "detail": _("The broadcaster is not recording.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = impl.stop_recording()
        if success and event_id:
            from src.apps.live.models import Event
            from src.apps.live.tasks import retrieve_recorded_video_task

            Event.objects.filter(pk=event_id).update(is_recording_stopped=True)
            retrieve_recorded_video_task.delay(int(event_id))

        return Response({"success": success}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Split recording",
        description="Split the current recording segment (Wowza only). Creates an intermediate video.",
        responses={
            200: {"type": "object", "properties": {"success": {"type": "boolean"}}}
        },
    )
    @action(detail=True, methods=["post"], url_path="split_record")
    def split_record(self, request, slug=None):
        """POST /api/live/broadcasters/{slug}/split_record/"""
        broadcaster = self.get_object()
        self.check_object_permissions(request, broadcaster)
        event_id = request.data.get("event_id")

        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return err
        if not impl.can_split():
            return Response(
                {
                    "detail": _(
                        "Split is not supported by this broadcaster's implementation."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not impl.is_recording(with_file_check=True):
            return Response(
                {"success": False, "detail": _("The broadcaster is not recording.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success = impl.split_recording()
        if success and event_id:
            from src.apps.live.tasks import retrieve_recorded_video_task

            retrieve_recorded_video_task.delay(int(event_id))

        return Response({"success": success}, status=status.HTTP_200_OK)

    @extend_schema(summary="Start stream", description="Start RTMP stream (SMP only).")
    @action(detail=True, methods=["post"], url_path="start_stream")
    def start_stream(self, request, slug=None):
        """POST /api/live/broadcasters/{slug}/start_stream/"""
        broadcaster = self.get_object()
        self.check_object_permissions(request, broadcaster)
        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return err
        if not impl.can_manage_stream():
            return Response(
                {"detail": _("Stream management not supported by this implementation.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Don't start if already streaming (matches V4 start_stream() logic)
        rtmp_infos = impl.get_stream_rtmp_infos()
        if rtmp_infos and rtmp_infos.get("is_streaming"):
            return Response({"success": True, "already_streaming": True})
        return Response({"success": impl.start_stream()})

    @extend_schema(summary="Stop stream", description="Stop RTMP stream (SMP only).")
    @action(detail=True, methods=["post"], url_path="stop_stream")
    def stop_stream(self, request, slug=None):
        """POST /api/live/broadcasters/{slug}/stop_stream/"""
        broadcaster = self.get_object()
        self.check_object_permissions(request, broadcaster)
        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return err
        if not impl.can_manage_stream():
            return Response(
                {"detail": _("Stream management not supported by this implementation.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Don't stop if not streaming (matches V4 stop_stream() logic)
        rtmp_infos = impl.get_stream_rtmp_infos()
        if rtmp_infos and not rtmp_infos.get("is_streaming"):
            return Response({"success": True, "already_stopped": True})
        return Response({"success": impl.stop_stream()})

    @extend_schema(
        summary="RTMP config",
        description="Return the RTMP stream configuration for this broadcaster (SMP only).",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {"type": "object"},
                },
            }
        },
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="rtmp_config",
        permission_classes=[permissions.IsAuthenticated],
    )
    def rtmp_config(self, request, slug=None):
        """GET /api/live/broadcasters/{slug}/rtmp_config/"""
        broadcaster = self.get_object()
        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return Response({"success": False, "error": "implementation error"})
        infos = impl.get_stream_rtmp_infos()
        if infos.get("error"):
            return Response({"success": False, "error": infos["error"]})
        return Response({"success": True, "data": infos})

    @extend_schema(
        summary="Recording status",
        description="Return whether the broadcaster is currently recording.",
        responses={
            200: {"type": "object", "properties": {"is_recording": {"type": "boolean"}}}
        },
    )
    @action(
        detail=True,
        methods=["get"],
        url_path="record_status",
        permission_classes=[permissions.IsAuthenticated],
    )
    def record_status(self, request, slug=None):
        """GET /api/live/broadcasters/{slug}/record_status/"""
        broadcaster = self.get_object()
        impl, err = self._get_piloting_or_error(broadcaster)
        if err:
            return Response({"is_recording": False})
        return Response({"is_recording": impl.is_recording(with_file_check=True)})
