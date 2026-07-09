"""
Esup-Pod - DublinCore viewset.
"""

from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from src.apps.video.conf import video_settings
from src.apps.video.models import Video
from src.apps.video.serializers import DublinCoreSerializer


class DublinCoreViewSet(viewsets.GenericViewSet):
    """
    Exposes Dublin Core metadata for all public videos on the current site.

    GET /api/dublin-core/          → paginated list
    GET /api/dublin-core/{slug}/   → single video
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = DublinCoreSerializer
    lookup_field = "slug"

    def get_queryset(self):
        """Returns published videos visible on the current site."""
        current_site = get_current_site(self.request)
        return (
            Video.objects.filter(
                status=Video.Status.PUBLISHED,
                sites=current_site,
            )
            .select_related("owner", "license", "language", "type")
            .prefetch_related("disciplines")
        )

    @extend_schema(
        summary="List Dublin Core metadata",
        responses={200: DublinCoreSerializer(many=True)},
    )
    def list(self, request):
        """GET /api/dublin-core/ — paginated list of Dublin Core records."""
        if not video_settings.use_dublin_core:
            return Response(
                {"detail": _("Dublin Core feature is disabled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [v.get_dublin_core() for v in page]
            return self.get_paginated_response(data)

        data = [v.get_dublin_core() for v in queryset]
        return Response(data)

    @extend_schema(
        summary="Retrieve Dublin Core metadata",
        responses={200: DublinCoreSerializer},
    )
    def retrieve(self, request, slug=None):
        """GET /api/dublin-core/{slug}/ — single video Dublin Core record."""
        if not video_settings.use_dublin_core:
            return Response(
                {"detail": _("Dublin Core feature is disabled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        video = self.get_queryset().filter(slug=slug).first()
        if not video:
            return Response(
                {"detail": _("Video not found.")}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(video.get_dublin_core())
