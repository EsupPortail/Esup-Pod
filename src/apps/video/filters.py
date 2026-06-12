"""
Esup-Pod - Video application FilterSets.

Provides generic, reusable FilterSet classes for filtering video resources
through the REST API using django-filters. Supports multi-value parameters
(e.g. ?tags__name=python&tags__name=django) for all filterable fields.
"""

import django_filters
from django_filters import rest_framework as filters

from src.apps.video.models import Video, Discipline


class MultiValueCharFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Allows filtering by multiple values for a single CharField.
    Usage: ?tags__name=python&tags__name=django
    """

    pass


class VideoFilterSet(django_filters.FilterSet):
    """
    FilterSet for the Video model.

    All list-type filters support multi-value query parameters.
    Example: GET /api/videos/?status=PU&status=DR&tags__name=python&tags__name=django
    """

    # --- Ownership ---
    owner__username = MultiValueCharFilter(
        field_name="owner__username",
        lookup_expr="in",
        label="Owner username(s) — multi-value supported",
    )

    # --- Status & Visibility ---
    status = django_filters.MultipleChoiceFilter(
        choices=Video.Status.choices,
        label="Publication status — multi-value supported (PU, DR, RE)",
    )
    is_auth_required = django_filters.BooleanFilter(
        field_name="is_auth_required",
        label="Requires authentication to view",
    )

    # --- Classification ---
    type__slug = MultiValueCharFilter(
        field_name="type__slug",
        lookup_expr="in",
        label="Video type slug(s) — multi-value supported",
    )
    cursus__slug = MultiValueCharFilter(
        field_name="cursus__slug",
        lookup_expr="in",
        label="Cursus slug(s) — multi-value supported",
    )
    discipline = django_filters.ModelMultipleChoiceFilter(
        field_name="disciplines",
        queryset=Discipline.objects.all(),
        label="Discipline ID(s) — multi-value supported",
    )

    # --- Tags ---
    tags__name = MultiValueCharFilter(
        field_name="tags__name",
        lookup_expr="in",
        label="Tag name(s) — multi-value supported",
    )
    tags__slug = MultiValueCharFilter(
        field_name="tags__slug",
        lookup_expr="in",
        label="Tag slug(s) — multi-value supported",
    )

    # --- Collection ---
    channel = django_filters.NumberFilter(
        field_name="channel_id",
        label="Channel ID",
    )

    # --- Date range ---
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Created after (ISO 8601 datetime)",
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Created before (ISO 8601 datetime)",
    )

    class Meta:
        """VideoFilterSet metadata."""

        model = Video
        fields = [
            "owner__username",
            "status",
            "is_auth_required",
            "type__slug",
            "cursus__slug",
            "discipline",
            "tags__name",
            "tags__slug",
            "channel",
            "created_at__gte",
            "created_at__lte",
        ]
