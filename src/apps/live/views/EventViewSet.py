"""
Esup-Pod - EventViewSet.
"""

import logging

from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.apps.live.models import Event, HeartBeat
from src.apps.live.serializers import EventSerializer
from src.apps.live.permissions import CanManageEvent, IsEventOwnerOrAdmin
from src.apps.live.conf import live_settings

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List upcoming events",
        description=(
            "Returns upcoming (non-draft, non-past) events for the current site. "
            "Supports filtering by `?broadcaster={id}` and `?type={slug}`."
        ),
    ),
    retrieve=extend_schema(
        summary="Get event",
        description="Returns event details. Draft events are only visible to their owners.",
    ),
    create=extend_schema(
        summary="Create event",
        description="Plan a new live event. Requires event management rights.",
    ),
    partial_update=extend_schema(
        summary="Update event",
        description="Update an event. Requires ownership.",
    ),
    destroy=extend_schema(
        summary="Delete event",
        description="Delete an event. Only the owner or a superuser may delete.",
    ),
)
class EventViewSet(viewsets.ModelViewSet):
    """
    Full CRUD ViewSet for live Events.

    GET  /api/live/events/                  — List upcoming events.
    GET  /api/live/my-events/               — List user's own events (via @action).
    GET  /api/live/events/{slug}/           — Event detail.
    POST /api/live/events/                  — Plan a new event.
    PATCH /api/live/events/{slug}/          — Update an event.
    DELETE /api/live/events/{slug}/         — Delete an event.
    POST /api/live/events/{slug}/unlock/    — Unlock a password-protected event.
    POST /api/live/events/{slug}/heartbeat/ — Send a viewer heartbeat ping.
    """

    serializer_class = EventSerializer
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ["title", "description"]
    filterset_fields = ["broadcaster", "type", "is_draft", "is_restricted"]
    ordering_fields = ["start_date", "end_date"]
    ordering = ["start_date"]

    def get_queryset(self):
        """Return events based on user role and visibility rules."""
        site = get_current_site(self.request)
        user = self.request.user

        # My events action: include all own events regardless of draft/past status
        if self.action == "my_events":
            if not user or not user.is_authenticated:
                return Event.objects.none()
            return (
                (
                    Event.objects.filter(broadcaster__building__sites=site).filter(
                        owner=user
                    )
                    | Event.objects.filter(
                        broadcaster__building__sites=site,
                        additional_owners=user,
                    )
                )
                .distinct()
                .select_related("broadcaster", "type", "owner")
            )

        qs = (
            Event.objects.filter(broadcaster__building__sites=site)
            .select_related("broadcaster", "type", "owner")
            .prefetch_related("restrict_access_to_groups")
        )

        if self.action == "list":
            qs = qs.filter(
                end_date__gt=timezone.now(),
                is_draft=False,
            )

        return qs

    def get_permissions(self):
        """Return appropriate permission classes based on the action being performed."""
        if self.action in ("create",):
            return [permissions.IsAuthenticated(), CanManageEvent()]
        if self.action in ("partial_update", "update", "destroy"):
            return [permissions.IsAuthenticated(), IsEventOwnerOrAdmin()]
        if self.action in ("my_events",):
            return [permissions.IsAuthenticated()]
        if self.action in ("heartbeat",):
            return [permissions.AllowAny()]
        if self.action in ("unlock",):
            return [permissions.AllowAny()]
        return [permissions.AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        """
        Return event detail.
        Applies access control: draft (hashkey), restricted (auth), groups.
        Password-protected events return 403 until unlocked.
        """
        event = self.get_object()
        user = request.user
        slug_private = request.query_params.get("key")

        if not self._check_access(request, event, slug_private):
            return Response(
                {"detail": _("You do not have access to this event.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        is_password_protected = bool(event.password)
        is_owner = user.is_authenticated and (
            event.owner == user
            or (user in event.additional_owners.all())
            or user.is_superuser
        )

        if is_password_protected and not is_owner:
            return Response(
                {
                    "detail": _(
                        "This event is password-protected. Use POST /unlock/ to gain access."
                    ),
                    "password_required": True,
                    "slug": event.slug,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(event)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """Assign the authenticated user as event owner on creation, and send confirmation email."""
        event = serializer.save(owner=self.request.user)
        if live_settings.email_on_event_scheduling:
            from src.apps.live.utils import send_email_confirmation

            try:
                send_email_confirmation(event)
            except Exception as exc:
                logger.warning("Failed to send event scheduling email: %s", exc)

    @extend_schema(
        summary="My events",
        description="Returns all events the authenticated user owns or co-owns (past and upcoming).",
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="my-events",
        permission_classes=[permissions.IsAuthenticated],
    )
    def my_events(self, request):
        """GET /api/live/my-events/"""
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    @extend_schema(
        summary="Get video cards for event",
        description="Return the list of videos linked to this event (as serialized data). "
        "Mirrors the V4 `event_get_video_cards` endpoint.",
    )
    @action(detail=True, methods=["get"], url_path="video-cards")
    def video_cards(self, request, slug=None):
        """GET /api/live/events/{slug}/video-cards/"""
        event = self.get_object()
        from src.apps.video.serializers import VideoSerializer

        videos = event.videos.all()
        serializer = VideoSerializer(videos, many=True, context={"request": request})
        return Response({"count": videos.count(), "results": serializer.data})

    @extend_schema(
        summary="Unlock event",
        description="Validate the password for a password-protected event. Returns 200 on success.",
        request={
            "application/json": {
                "type": "object",
                "properties": {"password": {"type": "string"}},
            }
        },
        responses={200: {"type": "object", "properties": {"detail": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post"], url_path="unlock")
    def unlock(self, request, slug=None):
        """POST /api/live/events/{slug}/unlock/"""
        event = self.get_object()
        if not event.password:
            return Response({"detail": _("This event is not password-protected.")})
        provided = request.data.get("password", "")
        if provided == event.password:
            return Response({"detail": _("Access granted.")}, status=status.HTTP_200_OK)
        return Response(
            {"detail": _("Incorrect password.")},
            status=status.HTTP_403_FORBIDDEN,
        )

    @extend_schema(
        summary="Send heartbeat",
        description=(
            "Send a periodic heartbeat ping to register this viewer as active. "
            f"Should be called every {live_settings.heartbeat_delay} seconds. "
            "Requires a unique `viewkey` string in the request body."
        ),
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "viewkey": {"type": "string"},
                },
            }
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "viewers": {"type": "integer"},
                    "heartbeat_delay": {"type": "integer"},
                },
            }
        },
    )
    @action(detail=True, methods=["post"], url_path="heartbeat")
    def heartbeat(self, request, slug=None):
        """
        POST /api/live/events/{slug}/heartbeat/

        The frontend must send a ping every HEARTBEAT_DELAY seconds with a
        stable unique `viewkey` (e.g. a UUID generated client-side).
        Stale heartbeats (2x the delay) are purged before counting.
        """
        event = self.get_object()
        viewkey = request.data.get("viewkey")
        if not viewkey:
            return Response(
                {"detail": _("'viewkey' is required.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Upsert heartbeat
        hb, created = HeartBeat.objects.get_or_create(
            viewkey=viewkey,
            defaults={"event": event},
        )
        if not created:
            hb.event = event
        if request.user.is_authenticated and not hb.user:
            hb.user = request.user
        from django.utils import timezone as tz

        hb.last_heartbeat = tz.now()
        hb.save()

        # Purge stale heartbeats and count active viewers
        HeartBeat.cleanup_stale(event, live_settings.heartbeat_delay)
        viewer_count = event.heartbeats.count()

        # Update max_viewers peak
        if viewer_count > event.max_viewers:
            Event.objects.filter(pk=event.pk).update(max_viewers=viewer_count)

        # Mirror V4 live_viewcounter: keep Event.viewers in sync with authenticated heartbeats
        if request.user.is_authenticated:
            event.viewers.add(request.user)

        return Response(
            {
                "viewers": viewer_count,
                "heartbeat_delay": live_settings.heartbeat_delay,
            },
            status=status.HTTP_200_OK,
        )

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _check_access(self, request, event: Event, slug_private: str | None) -> bool:
        """Return True if the requesting user may access the event."""
        user = request.user
        is_owner = user.is_authenticated and (
            event.owner == user
            or (user in event.additional_owners.all())
            or user.is_superuser
        )
        if is_owner:
            return True

        # Draft: only accessible via private hashkey
        if event.is_draft:
            if slug_private == event.get_hashkey():
                return True
            return False

        # Restricted: must be authenticated
        if event.is_restricted and not user.is_authenticated:
            return False

        # Group-restricted
        if event.restrict_access_to_groups.exists():
            if not user.is_authenticated:
                return False
            user_groups = set(user.groups.values_list("pk", flat=True))
            event_groups = set(
                event.restrict_access_to_groups.values_list("pk", flat=True)
            )
            if not user_groups & event_groups:
                return False

        return True
