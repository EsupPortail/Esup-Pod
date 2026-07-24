"""
Esup-Pod - ViewCount viewset.
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter

from src.apps.video.conf import video_settings
from src.apps.video.models import ViewCount
from src.apps.video.serializers import ViewCountSerializer


class ViewCountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for ViewCount records.
    Allows filtering by video slug and date range.

    GET /api/view-counts/?video=<slug>&date__gte=2026-01-01&date__lte=2026-06-30
    """

    serializer_class = ViewCountSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {"date": ["gte", "lte", "exact"]}
    ordering_fields = ["date", "count"]
    ordering = ["-date"]

    def get_permissions(self):
        """Requires authentication if VIEW_STATS_AUTH is enabled."""
        if video_settings.view_stats_auth:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        """Filters ViewCount records by video slug if provided."""
        video_slug = self.request.query_params.get("video")
        qs = ViewCount.objects.all()
        if video_slug:
            qs = qs.filter(video__slug=video_slug)
        return qs
