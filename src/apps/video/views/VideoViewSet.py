"""
Esup-Pod - Video viewset.
"""

import os
import logging
import hashlib

from rest_framework.response import Response
from rest_framework import viewsets, permissions, parsers, filters
from django.db.models import Q, F
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _
from django.http import FileResponse, Http404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.hashers import check_password
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)

from src.apps.video.models import Video
from src.apps.video.serializers import VideoSerializer
from src.apps.video.permissions import IsOwnerOrCoOwnerOrChannelCollaborator
from src.apps.authentication.permissions import IsSuperUser
from django_filters.rest_framework import DjangoFilterBackend
from src.apps.video.conf import video_settings
from src.apps.encoding.conf import encoding_settings
from src.apps.video.filters import VideoFilterSet

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List videos",
        description="Retrieve a list of videos. This endpoint supports advanced multi-value filtering. You can pass multiple values for the same parameter (e.g., `?tags__name=python&tags__name=django` or `?discipline=1&discipline=2`). Supported multi-value fields: `tags__name`, `tags__slug`, `type__slug`, `cursus__slug`, `discipline`, `status`, and `owner__username`.",
    )
)
class VideoViewSet(viewsets.ModelViewSet):
    """
    API view set for the Video model.
    """

    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrCoOwnerOrChannelCollaborator,
    ]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    lookup_field = "slug"
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["title", "description", "owner__username", "tags__name"]
    filterset_class = VideoFilterSet
    ordering_fields = ["created_at", "title", "view_count", "duration"]
    ordering = ["-created_at"]

    def get_object(self):
        """
        Override to accept slugs in V4 format (ex: 46859-titre-video).
        If the ID-slug format is detected, it attempts to retrieve by ID (pk).
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)

        if lookup_value and "-" in lookup_value:
            potential_id = lookup_value.split("-")[0]
            if potential_id.isdigit():
                obj = (
                    self.filter_queryset(self.get_queryset())
                    .filter(pk=potential_id)
                    .first()
                )
                if obj:
                    self.check_object_permissions(self.request, obj)
                    return obj

        return super().get_object()

    def get_queryset(self):
        """
        Filters videos based on the current site, authentication, ownership and visibility.
        Additional query-param filters (type, tags, disciplines, status, owner, etc.) are
        handled automatically by VideoFilterSet via DjangoFilterBackend.
        """
        user = self.request.user
        current_site = get_current_site(self.request)

        qs = Video.objects.filter(sites=current_site)

        if getattr(self, "action", None) in ["stream", "unlock", "register_view"]:
            return qs

        return (
            Video.objects.visible_for(user)
            .filter(id__in=qs)
            .prefetch_related(
                "contributions__contributor",
                "overlays",
                "documents",
            )
            .distinct()
        )

    def perform_create(self, serializer):
        """Creates a new video, checking user quota and triggering encoding."""
        user_videos = Video.objects.filter(owner=self.request.user).exclude(video_file="")
        total_bytes = sum(v.video_file.size for v in user_videos if v.video_file)
        incoming_file = self.request.FILES.get("video_file")
        incoming_size = incoming_file.size if incoming_file else 0
        max_quota_bytes = encoding_settings.user_quota_size_gb * 1024 * 1024 * 1024

        if total_bytes + incoming_size > max_quota_bytes:
            raise ValidationError(
                {
                    "video_file": _("Quota exceeded. You are limited to %(quota)s GB.")
                    % {"quota": encoding_settings.user_quota_size_gb}
                }
            )

        target_license = serializer.validated_data.get("license")
        if not target_license and video_settings.default_license:
            from src.apps.video.models import License

            try:
                target_license = License.objects.get(slug=video_settings.default_license)
            except License.DoesNotExist:
                target_license = None

        from src.apps.video.models import Type

        video_type = serializer.validated_data.get("type")
        if not video_type:
            try:
                video_type = Type.objects.get(id=video_settings.default_type_id)
            except Type.DoesNotExist:
                video_type = None

        video = serializer.save(
            owner=self.request.user,
            status=Video.Status.DRAFT,
            type=video_type,
            license=target_license,
        )

        current_site = get_current_site(self.request)
        video.sites.add(current_site)

        if video.video_file:
            from src.apps.encoding.tasks import trigger_runner_encoding_task

            site_url = video_settings.site_url.rstrip("/")
            source_url = f"{site_url}{video.video_file.url}"

            logger.debug("source_url: %s", source_url)

            trigger_runner_encoding_task.delay(video.pk, source_url)

    def _is_owner_or_admin(self, user, video):
        """Returns True if the user is superuser, owner, or co-owner."""
        if not user.is_authenticated:
            return False
        return (
            user.is_superuser
            or video.owner == user
            or video.co_owners.filter(pk=user.pk).exists()
        )

    def _check_group_restriction(self, user, video):
        """Checks if the user belongs to the allowed groups for the video."""
        if not user.is_authenticated:
            raise PermissionDenied(
                _("Authentication required to watch this group-restricted video.")
            )

        user_groups = user.owner.accessgroups.all() if hasattr(user, "owner") else []
        if not video.restricted_groups.filter(id__in=user_groups).exists():
            raise PermissionDenied(
                _("You do not belong to the allowed groups for this video.")
            )

    def _check_restricted_access(self, request, video):
        """Checks if the user can access a restricted video."""
        if video.is_auth_required and not request.user.is_authenticated:
            raise PermissionDenied(_("Authentication required to play this video."))
        if not video.password:
            return

        if request.session.get(f"video_unlocked_{video.id}"):
            return

        v4_hash = request.query_params.get("hash")
        if v4_hash:
            legacy_hash = hashlib.sha1(
                f"{settings.SECRET_KEY}{video.id}".encode()
            ).hexdigest()
            if v4_hash == legacy_hash:
                request.session[f"video_unlocked_{video.id}"] = True
                return

        raise PermissionDenied(_("Direct stream access forbidden. Password required."))

    def _check_stream_permissions(self, request, video):
        """Helper to check permissions for video streaming."""
        if self._is_owner_or_admin(request.user, video):
            return

        if video.restricted_groups.exists():
            self._check_group_restriction(request.user, video)
        elif video.status == Video.Status.RESTRICTED:
            self._check_restricted_access(request, video)
        elif video.status == Video.Status.DRAFT:
            raise PermissionDenied(_("This video is private."))

    def _get_video_file_to_stream(self, video, resolution=None):
        """Helper to find the appropriate video file for streaming."""
        if resolution:
            encoding = video.encodings.filter(resolution=resolution).first()
            if encoding and encoding.file:
                return encoding.file
        first_encoding = video.encodings.first()
        if first_encoding and first_encoding.file:
            return first_encoding.file
        return video.video_file

    @extend_schema(
        summary="Stream video file",
        parameters=[
            OpenApiParameter(
                name="resolution",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Target resolution for streaming (e.g., '1080', '720p', '360'). If specified without 'p', the backend automatically appends it.",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Video stream served successfully (progressive MP4 stream)."
            ),
            404: OpenApiResponse(
                description="Video file or specified resolution not found on disk."
            ),
        },
    )
    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def stream(self, request, slug=None):
        """
        Serves the video file as a progressive stream. Supports optional resolution filtering (e.g., 360p, 720p, 1080p).
        Falls back to the best available resolution if the requested one is not found.
        """
        video = self.get_object()
        self._check_stream_permissions(request, video)

        resolution = request.query_params.get("resolution")
        if resolution and not resolution.endswith("p"):
            resolution = f"{resolution}p"
        video_file_to_stream = self._get_video_file_to_stream(video, resolution)

        if not video_file_to_stream:
            raise Http404(_("Video file not found"))

        path = video_file_to_stream.path
        if not os.path.exists(path):
            raise Http404(_("Video file not found on disk"))

        file = open(path, "rb")
        response = FileResponse(file)
        response["Content-Type"] = "video/mp4"
        return response

    @extend_schema(
        summary="Register a video view",
        responses={
            200: OpenApiResponse(
                description="View registered successfully. Returns the updated total view count.",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "viewed"},
                        "total_count": {"type": "integer", "example": 105},
                    },
                },
            )
        },
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def register_view(self, request, slug=None):
        """
        Increments both the global view counter of the video and the daily views statistics (used for charts).
        """
        video = self.get_object()
        video.view_count = F("view_count") + 1
        video.save(update_fields=["view_count"])
        video.refresh_from_db()
        from datetime import date

        view_count_obj, created = video.view_counts.get_or_create(date=date.today())
        view_count_obj.count = F("count") + 1
        view_count_obj.save(update_fields=["count"])
        return Response({"status": "viewed", "total_count": video.view_count})

    @extend_schema(
        summary="Unlock restricted video",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "password": {
                        "type": "string",
                        "description": "Plain text password to unlock the video.",
                        "example": "securePassword123",
                    },
                    "hash": {
                        "type": "string",
                        "description": "Legacy V4 SHA1 security hash to bypass the password prompt.",
                        "example": "7c5a0c3b84138e1219b16828a2a7a409f584e03d",
                    },
                },
            }
        },
        parameters=[
            OpenApiParameter(
                name="hash",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optional legacy V4 SHA1 security hash passed via query parameters to unlock the stream.",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Video unlocked successfully. Returns the absolute URL of the video source file.",
                response={
                    "type": "object",
                    "properties": {
                        "video_url": {
                            "type": "string",
                            "format": "uri",
                            "example": "http://api.pod.univ.fr/media/video/sources/my-video.mp4",
                        },
                        "source": {
                            "type": "string",
                            "example": "legacy_hash",
                            "nullable": True,
                        },
                    },
                },
            ),
            403: OpenApiResponse(
                description="Incorrect password or invalid legacy hash.",
                response={
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string",
                            "example": "Incorrect password or hash",
                        }
                    },
                },
            ),
        },
    )
    @action(
        detail=True, methods=["get", "post"], permission_classes=[permissions.AllowAny]
    )
    def unlock(self, request, slug=None):
        """
        Unlocks a restricted/password-protected video using either a raw password in JSON body or a legacy V4 hash.
        """
        video = self.get_object()

        if video.status == Video.Status.RESTRICTED and video.is_auth_required:
            if not request.user.is_authenticated:
                raise PermissionDenied(_("You must be logged in to access this video."))
        v4_hash = request.query_params.get("hash") or request.data.get("hash")
        if v4_hash:
            legacy_hash = hashlib.sha1(
                f"{settings.SECRET_KEY}{video.id}".encode()
            ).hexdigest()
            if v4_hash == legacy_hash:
                request.session[f"video_unlocked_{video.id}"] = True
                url = (
                    request.build_absolute_uri(video.video_file.url)
                    if video.video_file
                    else None
                )
                return Response({"video_url": url, "source": "legacy_hash"})

        input_password = request.data.get("password")
        if video.password and check_password(input_password, video.password):
            request.session[f"video_unlocked_{video.id}"] = True
            url = (
                request.build_absolute_uri(video.video_file.url)
                if video.video_file
                else None
            )
            return Response({"video_url": url})
        return Response({"error": _("Incorrect password or hash")}, status=403)

    @extend_schema(
        summary="List my videos",
        responses={200: VideoSerializer(many=True)},
    )
    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """
        Returns only videos owned or co-owned by the current user.
        """
        user = request.user
        queryset = (
            self.get_queryset().filter(Q(owner=user) | Q(co_owners=user)).distinct()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Video metadata choices",
        responses={200: dict},
    )
    @action(detail=False, methods=["get"], permission_classes=[permissions.AllowAny])
    def metadata(self, request):
        """
        Returns available choices for License, Cursus, and Status to help the frontend.
        """
        from src.apps.video.models import License, Cursus, Language

        return Response(
            {
                "licenses": [
                    {"value": lic.slug, "label": lic.name}
                    for lic in License.objects.all()
                ],
                "cursus": [
                    {"value": c.slug, "label": c.name} for c in Cursus.objects.all()
                ],
                "statuses": [
                    {"value": c[0], "label": c[1]} for c in Video.Status.choices
                ],
                "languages": [
                    {"value": lang.slug, "label": lang.name}
                    for lang in Language.objects.all()
                ],
            }
        )

    @extend_schema(
        summary="Transfer video ownership",
        request={
            "application/json": {
                "type": "object",
                "properties": {"owner_id": {"type": "integer"}},
            }
        },
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}},
    )
    @action(detail=True, methods=["post"], permission_classes=[IsSuperUser])
    def transfer_ownership(self, request, slug=None):
        """
        Allows an admin to change the owner of a video.
        Accessible only by administrators.
        """
        video = self.get_object()
        new_owner_id = request.data.get("owner_id")

        if not new_owner_id:
            raise ValidationError({"owner_id": _("This field is required.")})

        from django.contrib.auth import get_user_model

        User = get_user_model()

        try:
            new_owner = User.objects.get(pk=new_owner_id)
        except User.DoesNotExist:
            raise ValidationError({"owner_id": _("User not found.")})

        video.owner = new_owner
        video.save(update_fields=["owner"])

        return Response({"status": "ownership transferred"})
