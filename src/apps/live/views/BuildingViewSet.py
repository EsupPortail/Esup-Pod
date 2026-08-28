"""
Esup-Pod - BuildingViewSet.
"""

from rest_framework import viewsets, permissions, filters
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.sites.shortcuts import get_current_site

from src.apps.live.models import Building
from src.apps.live.serializers import BuildingSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List buildings",
        description="Returns all buildings visible on the current site.",
    ),
    retrieve=extend_schema(
        summary="Get building", description="Returns details of a specific building."
    ),
)
class BuildingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/live/buildings/       — List buildings for the current site.
    GET /api/live/buildings/{id}/  — Retrieve a building.

    Write operations (POST/PATCH/DELETE) are reserved to staff via the Django admin.
    """

    serializer_class = BuildingSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self):
        """Filter buildings to the current site."""
        site = get_current_site(self.request)
        return (
            Building.objects.filter(sites=site)
            .prefetch_related("sites", "broadcaster_set")
            .order_by("name")
        )
