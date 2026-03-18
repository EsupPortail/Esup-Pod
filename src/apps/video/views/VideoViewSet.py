import os
import logging

from rest_framework.response import Response
from rest_framework import viewsets, permissions, parsers, filters
from django.db.models import Q
from src.apps.video.models import Video
from src.apps.video.serializers import VideoSerializer
from src.apps.video.permissions import IsOwnerOrCoOwnerOrReadOnly
from django.http import FileResponse, Http404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.hashers import check_password
from django.db.models import F
from src.apps.video.conf import video_settings
from src.apps.encoding.conf import encoding_settings
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class VideoViewSet(viewsets.ModelViewSet):
    """
    API view set for the Video model.
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

    def get_queryset(self):
        user = self.request.user
        qs = Video.objects.all()
        if not user.is_authenticated:
            q_filter = Q(status=Video.Status.PUBLISHED) | (
                Q(status=Video.Status.RESTRICTED) & Q(is_auth_required=False)
            )
            if not video_settings.homepage_shows_passworded:
                q_filter &= Q(password__isnull=True) | Q(password__exact="")
            return qs.filter(q_filter).distinct()
        if user.is_superuser:
            return qs

        # Authenticated users see:
        # - Published videos
        # - Restricted videos
        # - Their own videos (Drafts/Encoding/Error included)
        # - Videos they co-own
        return qs.filter(
            Q(status=Video.Status.PUBLISHED)
            | Q(status=Video.Status.RESTRICTED)
            | Q(owner=user)
            | Q(co_owners=user)
        ).distinct()

    def perform_create(self, serializer):
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

        licence_fournie = self.request.data.get("license")
        video = serializer.save(
            owner=self.request.user,
            status=Video.Status.ENCODING,
            license=(
                licence_fournie if licence_fournie else video_settings.default_license
            ),
        )

        if video.video_file:
            from src.apps.encoding.tasks import trigger_runner_encoding_task
            from django.conf import settings

            site_url = getattr(settings, "SITE_URL", "http://api:8000").rstrip("/")
            source_url = f"{site_url}{video.video_file.url}"

            logger.debug("source_url: %s", source_url)

            trigger_runner_encoding_task.delay(video.pk, source_url)

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def stream(self, request, slug=None):
        from django.shortcuts import get_object_or_404

        video = get_object_or_404(Video, slug=slug)
        user = request.user
        is_owner_or_admin = user.is_authenticated and (
            user.is_superuser
            or video.owner == user
            or video.co_owners.filter(pk=user.pk).exists()
        )
        if not is_owner_or_admin:
            if video.status == Video.Status.RESTRICTED:
                if video.is_auth_required and not user.is_authenticated:
                    raise PermissionDenied("Authentication required to play this video.")
                if video.password:
                    raise PermissionDenied(
                        "Direct stream access forbidden. Password required."
                    )
            elif video.status == Video.Status.DRAFT:
                raise PermissionDenied("This video is private.")
        if not video.video_file:
            raise Http404("Video file not found")
        path = video.video_file.path
        if not os.path.exists(path):
            raise Http404("Video file not found on disk")
        file = open(path, "rb")
        response = FileResponse(file)
        response["Content-Type"] = "video/mp4"
        return response

    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def register_view(self, request, slug=None):
        from django.shortcuts import get_object_or_404

        video = get_object_or_404(Video, slug=slug)
        video.view_count = F("view_count") + 1
        video.save(update_fields=["view_count"])
        video.refresh_from_db()
        from datetime import date

        view_count_obj, created = video.view_counts.get_or_create(date=date.today())
        view_count_obj.count = F("count") + 1
        view_count_obj.save(update_fields=["count"])
        return Response({"status": "viewed", "total_count": video.view_count})

    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def unlock(self, request, slug=None):
        """
        Unlocks a RESTRICTED video with a password.
        """
        from django.shortcuts import get_object_or_404

        video = get_object_or_404(Video, slug=slug)
        if video.status == Video.Status.RESTRICTED and video.is_auth_required:
            if not request.user.is_authenticated:
                raise PermissionDenied("You must be logged in to access this video.")
        input_password = request.data.get("password")
        if video.password and check_password(input_password, video.password):
            url = (
                request.build_absolute_uri(video.video_file.url)
                if video.video_file
                else None
            )
            return Response({"video_url": url})
        return Response({"error": "Incorrect password"}, status=403)
