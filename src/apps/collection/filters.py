"""
Esup-Pod - Collection application FilterSets.

Provides generic, reusable FilterSet classes for Channel and Playlist resources.
Follows the same pattern as VideoFilterSet — multi-value support via
MultiValueCharFilter for all applicable fields.
"""

import django_filters
from django_filters import rest_framework as filters
from django.utils.translation import gettext_lazy as _

from src.apps.collection.models import Channel, Playlist


class MultiValueCharFilter(filters.BaseInFilter, filters.CharFilter):
    """
    Allows filtering by multiple values for a single CharField.
    Usage: ?owner__username=alice&owner__username=bob
    """

    pass


class ChannelFilterSet(django_filters.FilterSet):
    """
    FilterSet for the Channel model.

    Example: GET /api/channels/?is_public=true&owner__username=alice
    """

    owner__username = MultiValueCharFilter(
        field_name="owner__username",
        lookup_expr="in",
        label=_("Owner username(s) — multi-value supported"),
    )
    is_public = django_filters.BooleanFilter(
        field_name="is_public",
        label=_("Public channels only"),
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label=_("Created after (ISO 8601 datetime)"),
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label=_("Created before (ISO 8601 datetime)"),
    )

    class Meta:
        """ChannelFilterSet metadata."""

        model = Channel
        fields = [
            "owner__username",
            "is_public",
            "created_at__gte",
            "created_at__lte",
        ]


class PlaylistFilterSet(django_filters.FilterSet):
    """
    FilterSet for the Playlist model.

    Example: GET /api/playlists/?is_public=true&owner__username=alice
    """

    owner__username = MultiValueCharFilter(
        field_name="owner__username",
        lookup_expr="in",
        label=_("Owner username(s) — multi-value supported"),
    )
    is_public = django_filters.BooleanFilter(
        field_name="is_public",
        label=_("Public playlists only"),
    )
    is_protected = django_filters.BooleanFilter(
        method="filter_is_protected",
        label=_("Has password protection"),
    )
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label=_("Created after (ISO 8601 datetime)"),
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label=_("Created before (ISO 8601 datetime)"),
    )

    def filter_is_protected(self, queryset, name, value):
        """Filter playlists by password-protection status."""
        if value:
            return queryset.exclude(password__isnull=True).exclude(password__exact="")
        return queryset.filter(password__isnull=True) | queryset.filter(
            password__exact=""
        )

    class Meta:
        """PlaylistFilterSet metadata."""

        model = Playlist
        fields = [
            "owner__username",
            "is_public",
            "is_protected",
            "created_at__gte",
            "created_at__lte",
        ]
