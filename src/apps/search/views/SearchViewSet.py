"""
Esup-Pod - Search ViewSet.

Exposes the /api/search/ endpoint for full-text video search
backed by Redis Search.

Equivalent to V4's pod/video_search/views.py search_videos() view.

Supported query parameters:
  q            - Full-text search query
  type         - Filter by type slug
  discipline   - Filter by discipline slug (multi-value)
  channel      - Filter by channel slug (multi-value)
  theme        - Filter by theme slug (multi-value)
  tag          - Filter by tag slug (multi-value)
  owner        - Filter by owner username
  cursus       - Filter by cursus slug
  lang         - Filter by main language code
  mediatype    - "video" | "audio"
  date_from    - Unix timestamp (inclusive lower bound on date_added)
  date_to      - Unix timestamp (inclusive upper bound on date_added)
  page         - Page number (0-indexed, max 500)
  site_id      - Filter by site ID (multi-site support)
"""

import logging
from typing import Optional

from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import permissions, viewsets, serializers
from rest_framework.response import Response

from src.apps.video.models import Video
from src.apps.video.serializers import VideoSerializer
from src.apps.search.conf import search_settings
from src.apps.search.services.query import SearchFilters, search_videos

logger = logging.getLogger(__name__)

# OpenAPI parameter definitions
_SEARCH_PARAMS = [
    OpenApiParameter("q", str, description="Full-text search query string."),
    OpenApiParameter("type", str, description="Filter by video type slug."),
    OpenApiParameter(
        "discipline",
        str,
        many=True,
        description="Filter by discipline slug (multi-value).",
    ),
    OpenApiParameter(
        "channel", str, many=True, description="Filter by channel slug (multi-value)."
    ),
    OpenApiParameter(
        "theme", str, many=True, description="Filter by theme slug (multi-value)."
    ),
    OpenApiParameter(
        "tag", str, many=True, description="Filter by tag slug (multi-value)."
    ),
    OpenApiParameter("owner", str, description="Filter by owner username."),
    OpenApiParameter("cursus", str, description="Filter by cursus slug."),
    OpenApiParameter(
        "lang", str, description="Filter by main language code (e.g. 'fr')."
    ),
    OpenApiParameter("mediatype", str, description="'video' or 'audio'."),
    OpenApiParameter(
        "date_from",
        int,
        description="Filter: only videos added on or after this Unix timestamp.",
    ),
    OpenApiParameter(
        "date_to",
        int,
        description="Filter: only videos added on or before this Unix timestamp.",
    ),
    OpenApiParameter(
        "page",
        int,
        description="Page number (0-indexed). Max 500.",
    ),
]


class SearchViewSet(viewsets.GenericViewSet):
    """
    ViewSet providing the video search endpoint backed by Redis Search.
    Replaces the Elasticsearch-based search from V4.

    Only the `list` action is exposed (GET /api/search/).
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = VideoSerializer
    # No queryset needed at class level — overridden in list()

    @extend_schema(
        summary="Search videos",
        description=(
            "Full-text search over the video catalog using Redis Search. "
            "Supports field-level filtering, pagination, and faceted aggregations. "
            "Equivalent to the V4 Elasticsearch search endpoint.\n\n"
            "**1. Full-text search**\n"
            "Search for text in titles, descriptions, and tags:\n"
            "`GET /api/search/?q=maths`\n\n"
            "**2. Filtering (Facets)**\n"
            "You can combine multiple filters. If you pass the same parameter multiple times, it acts as an **OR** condition (e.g., videos that have tag A OR tag B).\n"
            "`GET /api/search/?type=cours&tag=maths&tag=physique`\n\n"
            "**3. Pagination**\n"
            "The endpoint is paginated. Use the `page` parameter (0-indexed).\n"
            "`GET /api/search/?q=maths&page=1`\n\n"
            "**4. Facets (Buckets)**\n"
            "The response automatically includes a `facets` dictionary. This contains the available filters and the count of videos for each filter, based on the current search criteria. "
            "You can use this to dynamically build the sidebar filters in the frontend UI.\n\n"
            "---\n"
            "*Note: When `SEARCH_ENGINE=disabled`, the endpoint always returns empty results. "
            "When `SEARCH_ENGINE=database`, a basic Django ORM full-text search is used without facets.*"
        ),
        parameters=_SEARCH_PARAMS,
        responses={
            200: OpenApiResponse(
                description="Search results with pagination and optional facets.",
                response=inline_serializer(
                    name="SearchResponse",
                    fields={
                        "count": serializers.IntegerField(
                            help_text="Total number of videos matching the search."
                        ),
                        "results": VideoSerializer(
                            many=True,
                            help_text="List of video objects for the current page.",
                        ),
                        "facets": serializers.DictField(
                            child=serializers.ListField(
                                child=inline_serializer(
                                    name="FacetBucket",
                                    fields={
                                        "value": serializers.CharField(
                                            help_text="The facet bucket label."
                                        ),
                                        "count": serializers.IntegerField(
                                            help_text="Number of videos in this bucket."
                                        ),
                                    },
                                )
                            ),
                            help_text="Faceted aggregations (buckets) for various fields.",
                        ),
                        "has_next": serializers.BooleanField(
                            help_text="True if there is a next page of results."
                        ),
                        "next_page": serializers.IntegerField(
                            help_text="The index of the next page (to pass as 'page' param)."
                        ),
                        "query": serializers.CharField(
                            help_text="The full-text query that was executed."
                        ),
                    },
                ),
            ),
            503: OpenApiResponse(description="Redis Search unavailable."),
        },
    )
    def list(self, request):
        """
        GET /api/search/?q=<query>&type=<slug>&...
        Returns paginated video results with facet counts.
        """
        # --- Short-circuit: search disabled ---
        if search_settings.is_disabled:
            return Response(
                {
                    "count": 0,
                    "results": [],
                    "facets": {},
                    "has_next": False,
                    "next_page": 0,
                    "query": "",
                }
            )

        # --- Parse query parameters ---
        filters = _parse_filters(request)

        # --- Execute search ---
        if search_settings.is_redis:
            try:
                result = search_videos(filters)
            except Exception as exc:
                logger.error("Search engine error: %s", exc)
                return Response(
                    {"detail": _("Search service temporarily unavailable.")},
                    status=503,
                )
        else:
            # Fallback: basic database search
            result = _database_search(filters)

        # --- Retrieve Video objects from DB using the ordered PKs from Redis ---
        if result.video_ids:
            # Preserve Redis ordering using Case/When
            from django.db.models import Case, IntegerField, Value, When

            preserved_order = Case(
                *[
                    When(pk=pk, then=Value(idx))
                    for idx, pk in enumerate(result.video_ids)
                ],
                output_field=IntegerField(),
            )
            videos = Video.objects.filter(pk__in=result.video_ids).order_by(
                preserved_order
            )
        else:
            videos = Video.objects.none()

        serializer = VideoSerializer(videos, many=True, context={"request": request})

        return Response(
            {
                "count": result.total,
                "results": serializer.data,
                "facets": _serialize_facets(result.facets),
                "has_next": result.has_next,
                "next_page": result.next_page,
                "query": filters.query,
            }
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_filters(request) -> SearchFilters:
    """Extracts search parameters from the incoming HTTP request."""
    # Site ID (multi-site support, V5 addition)
    try:
        current_site_id: Optional[int] = get_current_site(request).id
    except Exception:
        current_site_id = None

    # Pagination — clamp to [0, SEARCH_MAX_PAGE]
    page_raw = request.GET.get("page", "0")
    try:
        page = max(0, min(int(page_raw), search_settings.search_max_page))
    except ValueError:
        page = 0

    # Date timestamps
    def _ts(param: str) -> Optional[int]:
        """Convert a query parameter to a Unix timestamp."""
        val = request.GET.get(param)
        if val:
            try:
                return int(val)
            except ValueError:
                return None
        return None

    return SearchFilters(
        query=request.GET.get("q", "").strip(),
        type_slug=request.GET.get("type") or None,
        disciplines=request.GET.getlist("discipline"),
        channels=request.GET.getlist("channel"),
        themes=request.GET.getlist("theme"),
        tags=request.GET.getlist("tag"),
        owner_username=request.GET.get("owner") or None,
        cursus_slug=request.GET.get("cursus") or None,
        main_lang=request.GET.get("lang") or None,
        mediatype=request.GET.get("mediatype") or None,
        date_from=_ts("date_from"),
        date_to=_ts("date_to"),
        site_id=current_site_id,
        page=page,
    )


def _database_search(filters: SearchFilters):
    """
    Minimal fallback search using Django ORM (SEARCH_ENGINE=database).
    Returns the same SearchResult structure as the Redis backend.
    """
    from django.db.models import Q
    from src.apps.search.services.query import SearchResult

    qs = Video.objects.filter(status=Video.Status.PUBLISHED)

    if filters.site_id:
        qs = qs.filter(sites__id=filters.site_id)

    if filters.query and len(filters.query) >= search_settings.search_min_query_length:
        qs = qs.filter(
            Q(title__icontains=filters.query)
            | Q(description__icontains=filters.query)
            | Q(tags__name__icontains=filters.query)
        ).distinct()

    if filters.type_slug:
        qs = qs.filter(type__slug=filters.type_slug)

    if filters.disciplines:
        qs = qs.filter(disciplines__slug__in=filters.disciplines).distinct()

    if filters.channels:
        qs = qs.filter(channel__slug__in=filters.channels).distinct()

    if filters.main_lang:
        qs = qs.filter(language__slug=filters.main_lang)

    if filters.cursus_slug:
        qs = qs.filter(cursus__slug=filters.cursus_slug)

    total = qs.count()
    size = search_settings.search_results_per_page
    offset = filters.page * size
    video_ids = list(
        qs.order_by("-created_at")[offset : offset + size].values_list("pk", flat=True)
    )

    return SearchResult(
        video_ids=video_ids,
        total=total,
        has_next=(filters.page + 1) * size < total,
        next_page=filters.page + 1,
        facets={},
        query=filters.query,
    )


def _serialize_facets(facets: dict) -> dict:
    """Converts FacetValue dataclasses to plain dicts for JSON serialization."""
    return {
        name: [{"value": f.value, "count": f.count} for f in buckets]
        for name, buckets in facets.items()
    }
