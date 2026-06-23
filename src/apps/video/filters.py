"""
Esup-Pod - Video application FilterSets.

Provides generic, reusable FilterSet classes for filtering video resources
through the REST API using django-filters. Supports multi-value parameters
(e.g. ?tags__name=python&tags__name=django) for all filterable fields.
"""

import django_filters
from django_filters import rest_framework as filters
from django.utils.translation import gettext_lazy as _

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
        label=_("Owner username(s)"),
        help_text=_(
            "Filter videos by one or more owner usernames. Multiple values can be comma-separated or repeated, e.g. ?owner__username=user1,user2"
        ),
    )

    # --- Status & Visibility ---
    status = django_filters.MultipleChoiceFilter(
        choices=Video.Status.choices,
        label=_("Publication status"),
        help_text=_(
            "Filter videos by publication status. Multiple statuses can be specified. Choices are: PU (Public), DR (Draft), RE (Restricted)."
        ),
    )
    is_auth_required = django_filters.BooleanFilter(
        field_name="is_auth_required",
        label=_("Authentication requirement"),
        help_text=_(
            "Filter videos based on whether authentication is required to view them (true or false)."
        ),
    )

    # --- Classification ---
    type__slug = MultiValueCharFilter(
        field_name="type__slug",
        lookup_expr="in",
        label=_("Video type slug(s)"),
        help_text=_(
            "Filter videos by type slug(s). Multiple values are supported, e.g. ?type__slug=course,conference"
        ),
    )
    cursus__slug = MultiValueCharFilter(
        field_name="cursus__slug",
        lookup_expr="in",
        label=_("Cursus slug(s)"),
        help_text=_(
            "Filter videos by cursus slug(s). Multiple values are supported, e.g. ?cursus__slug=l1,l2"
        ),
    )
    discipline = django_filters.ModelMultipleChoiceFilter(
        field_name="disciplines",
        queryset=Discipline.objects.all(),
        label=_("Discipline ID(s)"),
        help_text=_(
            "Filter videos by discipline database ID(s). Multiple values are supported, e.g. ?discipline=1,2"
        ),
    )

    # --- Tags ---
    tags__name = MultiValueCharFilter(
        field_name="tags__name",
        lookup_expr="in",
        label=_("Tag name(s)"),
        help_text=_(
            "Filter videos by tag name(s). Multiple tag names are supported, e.g. ?tags__name=python,django"
        ),
    )
    tags__slug = MultiValueCharFilter(
        field_name="tags__slug",
        lookup_expr="in",
        label=_("Tag slug(s)"),
        help_text=_(
            "Filter videos by tag slug(s). Multiple tag slugs are supported, e.g. ?tags__slug=python,django"
        ),
    )

    # --- Collection ---
    channel = django_filters.NumberFilter(
        field_name="channel_id",
        label=_("Channel ID"),
        help_text=_("Filter videos belonging to a specific channel by its database ID."),
    )

    # --- Date range ---
    created_at__gte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label=_("Created after"),
        help_text=_(
            "Filter videos created on or after this ISO 8601 datetime, e.g. 2026-06-18T10:00:00Z"
        ),
    )
    created_at__lte = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label=_("Created before"),
        help_text=_(
            "Filter videos created on or before this ISO 8601 datetime, e.g. 2026-06-18T12:00:00Z"
        ),
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
