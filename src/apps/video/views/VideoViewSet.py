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
from django.http import FileResponse, Http404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.contrib.auth.hashers import check_password
from drf_spectacular.utils import extend_schema

from src.apps.video.models import Video
from src.apps.video.serializers import VideoSerializer
from src.apps.video.permissions import IsOwnerOrCoOwnerOrReadOnly
from src.apps.video.conf import video_settings
from src.apps.encoding.conf import encoding_settings

logger = logging.getLogger(__name__)


class VideoViewSet(viewsets.ModelViewSet):
    """
    Esup-Pod - API view set for the Video model.
    """

    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrCoOwnerOrReadOnly,
    ]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "owner__username"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_object(self):
        """
        Surcharge pour accepter les slugs au format V4 (ex: 46859-titre-video).
        Si on détecte le format ID-slug, on tente de récupérer par ID (pk).
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)

        if lookup_value and "-" in lookup_value:
            potential_id = lookup_value.split("-")[0]
            if potential_id.isdigit():
                obj = Video.objects.filter(pk=potential_id).first()
                if obj:
                    self.check_object_permissions(self.request, obj)
                    return obj

        return super().get_object()

    def _apply_query_filters(self, qs):
        """Helper to apply GET query parameters filters."""
        type_slug = self.request.query_params.get("type__slug")
        if type_slug:
            qs = qs.filter(type__slug=type_slug)

        discipline_id = self.request.query_params.get("discipline")
        if discipline_id:
            qs = qs.filter(disciplines__id=discipline_id)

        tags_slug = self.request.query_params.get("tags__slug")
        if tags_slug:
            qs = qs.filter(tags__slug=tags_slug)

        tags_name = self.request.query_params.get("tags__name")
        if tags_name:
            qs = qs.filter(tags__name=tags_name)

        return qs

    def _get_visibility_filter(self, user):
        """Returns Q object representing video visibility for the user."""
        if not user.is_authenticated:
            q_filter = Q(status=Video.Status.PUBLISHED) | (
                Q(status=Video.Status.RESTRICTED) & Q(is_auth_required=False)
            )
            if not video_settings.homepage_shows_passworded:
                q_filter &= Q(password__isnull=True) | Q(password__exact="")
            return q_filter

        base_q = (
            Q(status=Video.Status.PUBLISHED)
            | Q(status=Video.Status.RESTRICTED)
            | Q(owner=user)
            | Q(co_owners=user)
        )
        if hasattr(user, "owner"):
            base_q |= Q(restricted_groups__users=user.owner)
        return base_q

    def get_queryset(self):
        """Filters videos based on the current site, authentication, ownership and visibility."""
        user = self.request.user
        current_site = get_current_site(self.request)

        qs = Video.objects.filter(sites=current_site)
        qs = self._apply_query_filters(qs)

        if getattr(self, "action", None) in ["stream", "unlock", "register_view"]:
            return qs

        if user.is_authenticated and user.is_superuser:
            return qs

        visibility_q = self._get_visibility_filter(user)
        return qs.filter(visibility_q).distinct()

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
                    "video_file": f"Quota exceeded. You are limited to {encoding_settings.user_quota_size_gb} GB."
                }
            )

        provided_license = self.request.data.get("license")

        from src.apps.video.models import Type

        video_type = serializer.validated_data.get("type")
        if not video_type:
            try:
                video_type = Type.objects.get(id=video_settings.default_type_id)
            except Type.DoesNotExist:
                video_type = None

        video = serializer.save(
            owner=self.request.user,
            status=Video.Status.ENCODING,
            type=video_type,
            license=(
                provided_license if provided_license else video_settings.default_license
            ),
        )

        current_site = get_current_site(self.request)
        video.sites.add(current_site)

        if video.video_file:
            from src.apps.encoding.tasks import trigger_runner_encoding_task

            site_url = getattr(settings, "SITE_URL", "http://api:8000").rstrip("/")
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
                "Authentication required to watch this group-restricted video."
            )

        user_groups = user.owner.accessgroups.all() if hasattr(user, "owner") else []
        if not video.restricted_groups.filter(id__in=user_groups).exists():
            raise PermissionDenied(
                "You do not belong to the allowed groups for this video."
            )

    def _check_restricted_access(self, request, video):
        """Checks if the user can access a restricted video."""
        if video.is_auth_required and not request.user.is_authenticated:
            raise PermissionDenied("Authentication required to play this video.")
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

        raise PermissionDenied("Direct stream access forbidden. Password required.")

    def _check_stream_permissions(self, request, video):
        """Helper to check permissions for video streaming."""
        if self._is_owner_or_admin(request.user, video):
            return

        if video.restricted_groups.exists():
            self._check_group_restriction(request.user, video)
        elif video.status == Video.Status.RESTRICTED:
            self._check_restricted_access(request, video)
        elif video.status == Video.Status.DRAFT:
            raise PermissionDenied("This video is private.")

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

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def stream(self, request, slug=None):
        """Serves the video file as a stream."""
        video = self.get_object()
        self._check_stream_permissions(request, video)

        resolution = request.query_params.get("resolution")
        video_file_to_stream = self._get_video_file_to_stream(video, resolution)

        if not video_file_to_stream:
            raise Http404("Video file not found")

        path = video_file_to_stream.path
        if not os.path.exists(path):
            raise Http404("Video file not found on disk")

        file = open(path, "rb")
        response = FileResponse(file)
        response["Content-Type"] = "video/mp4"
        return response

    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def register_view(self, request, slug=None):
        """Increments the view count for the video and daily statistics."""
        video = self.get_object()
        video.view_count = F("view_count") + 1
        video.save(update_fields=["view_count"])
        video.refresh_from_db()
        from datetime import date

        view_count_obj, created = video.view_counts.get_or_create(date=date.today())
        view_count_obj.count = F("count") + 1
        view_count_obj.save(update_fields=["count"])
        return Response({"status": "viewed", "total_count": video.view_count})

    @action(
        detail=True, methods=["get", "post"], permission_classes=[permissions.AllowAny]
    )
    def unlock(self, request, slug=None):
        """
        Unlocks a RESTRICTED video with a password or legacy V4 hash.
        """
        video = self.get_object()

        if video.status == Video.Status.RESTRICTED and video.is_auth_required:
            if not request.user.is_authenticated:
                raise PermissionDenied("You must be logged in to access this video.")
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
        return Response({"error": "Incorrect password or hash"}, status=403)

    @extend_schema(
        summary="List my videos",
        description="Returns only videos owned or co-owned by the current user.",
        responses={200: VideoSerializer(many=True)},
    )
    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        """
        Retrieves a filtered list of videos where the current user is either the owner or a co-owner.
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
