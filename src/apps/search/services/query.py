"""
Esup-Pod - Search query service.

Builds and executes FT.SEARCH + FT.AGGREGATE queries against Redis Search.
Equivalent to the search_videos() view + get_filter_search() logic in V4.

V4 facets replicated:
  owner_full_name, type_title, disciplines_title,
  tags_name, channels_title, cursus, main_lang
  + themes_title (new in V5)
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from django.core.cache import cache

from redis.commands.search.aggregation import AggregateRequest, Desc
from redis.commands.search import reducers
from redis.commands.search.query import Query

from src.apps.search.conf import search_settings
from src.apps.search.services.indexer import get_redis_client

logger = logging.getLogger(__name__)

# Cache TTL for facets (short: new videos must appear quickly)
FACETS_CACHE_TTL = 120  # 2 minutes
# Cache TTL for search results
SEARCH_CACHE_TTL = 60  # 1 minute

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SearchFilters:
    """Parsed search filters from request query params."""

    query: str = ""  # Full-text query string
    type_slug: Optional[str] = None  # Filter by video type slug
    disciplines: List[str] = field(default_factory=list)
    channels: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    owner_username: Optional[str] = None
    cursus_slug: Optional[str] = None
    main_lang: Optional[str] = None
    mediatype: Optional[str] = None  # "video" | "audio"
    date_from: Optional[int] = None  # Unix timestamp
    date_to: Optional[int] = None  # Unix timestamp
    site_id: Optional[int] = None
    page: int = 0


@dataclass
class FacetValue:
    """A single facet bucket (label + count)."""

    value: str
    count: int


@dataclass
class SearchResult:
    """Structured response returned by search_videos()."""

    video_ids: List[int]
    total: int
    has_next: bool
    next_page: int
    facets: Dict[str, List[FacetValue]]
    query: str


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------

# Facet definitions: (redis_field, display_name)
FACET_FIELDS: List[Tuple[str, str]] = [
    ("type_slug", "type"),
    ("disciplines_slug", "disciplines"),
    ("channels_slug", "channels"),
    ("themes_slug", "themes"),
    ("tags_slug", "tags"),
    ("owner_username_tag", "owner"),
    ("cursus_slug", "cursus"),
    ("main_lang", "lang"),
]


def _build_ft_query(filters: SearchFilters) -> str:  # noqa: C901
    """
    Builds a Redis FT.SEARCH query string from the given filters.

    Full-text: @title|@description|... (Redis Search handles WEIGHT automatically)
    TAG filters: @type_slug:{cours}
    NUMERIC filters: @date_added_ts:[ts1 ts2]
    """
    parts = []

    # --- Full-text query ---
    if filters.query and len(filters.query) >= search_settings.search_min_query_length:
        # Escape special Redis Search characters to avoid syntax errors
        q = filters.query.replace("-", "\\-").replace("@", "\\@")
        parts.append(q)
    else:
        # Match all (equivalent to V4's "match_all": {})
        parts.append("*")

    # --- TAG filters ---
    def _tag_filter(field_name: str, value: str) -> str:
        return f"@{field_name}:{{{value}}}"

    def _multi_tag_filter(field_name: str, values: List[str]) -> str:
        """Builds an OR filter for multiple tags."""
        joined = "|".join(values)
        return f"@{field_name}:{{{joined}}}"

    if filters.type_slug:
        parts.append(_tag_filter("type_slug", filters.type_slug))

    if filters.disciplines:
        for slug in filters.disciplines:
            parts.append(_tag_filter("disciplines_slug", slug))

    if filters.channels:
        for slug in filters.channels:
            parts.append(_tag_filter("channels_slug", slug))

    if filters.themes:
        for slug in filters.themes:
            parts.append(_tag_filter("themes_slug", slug))

    if filters.tags:
        for slug in filters.tags:
            parts.append(_tag_filter("tags_slug", slug))

    if filters.owner_username:
        parts.append(_tag_filter("owner_username_tag", filters.owner_username))

    if filters.cursus_slug:
        parts.append(_tag_filter("cursus_slug", filters.cursus_slug))

    if filters.main_lang:
        parts.append(_tag_filter("main_lang", filters.main_lang))

    if filters.mediatype:
        parts.append(_tag_filter("mediatype", filters.mediatype))

    if filters.site_id is not None:
        parts.append(_tag_filter("site_id", str(filters.site_id)))

    # --- NUMERIC SORTABLE filters (date range — V4: start_date/end_date) ---
    if filters.date_from is not None or filters.date_to is not None:
        low = filters.date_from if filters.date_from is not None else "-inf"
        high = filters.date_to if filters.date_to is not None else "+inf"
        parts.append(f"@date_added_ts:[{low} {high}]")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main search function
# ---------------------------------------------------------------------------


def _make_cache_key(prefix: str, q_str: str, page: int = 0) -> str:
    """Build a stable cache key from the Redis query string and page number."""
    digest = hashlib.md5(f"{q_str}:{page}".encode()).hexdigest()
    return f"pod:search:{prefix}:{digest}"


def search_videos(filters: SearchFilters) -> SearchResult:
    """
    Executes an FT.SEARCH query and returns structured results.
    Equivalent to search_videos() view in V4.

    Returns video PKs (not full objects) — DRF views are responsible for
    fetching the actual Video queryset from the DB.

    Results are cached in Redis (TTL=60s) to reduce load on Redis Search
    — same cache-aside pattern as V4 on Elasticsearch.
    """
    size = search_settings.search_results_per_page
    page = min(filters.page, search_settings.search_max_page)
    offset = page * size

    q_str = _build_ft_query(filters)

    # --- Check cache before querying Redis Search ---
    cache_key = _make_cache_key("results", q_str, page)
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache HIT search_videos — key=%s", cache_key)
        return cached

    client = get_redis_client()

    try:
        query = (
            Query(q_str)
            .paging(offset, size)
            .sort_by(
                "date_added_ts", asc=False
            )  # Most recent first (like V4 gauss decay)
            .return_fields("video_id")
            .dialect(2)
        )

        result = client.ft(search_settings.search_index_name).search(query)
        total = result.total

        video_ids = []
        for doc in result.docs:
            try:
                video_ids.append(int(doc.video_id))
            except (AttributeError, ValueError):
                pass

    except Exception as exc:
        logger.error("Redis FT.SEARCH error: %s", exc)
        return SearchResult(
            video_ids=[],
            total=0,
            has_next=False,
            next_page=0,
            facets={},
            query=q_str,
        )

    # --- Facets (equiv. V4 aggs) ---
    facets: Dict[str, List[FacetValue]] = {}
    if search_settings.search_enable_facets:
        facets = _get_facets(client, q_str)

    has_next = (page + 1) * size < total

    search_result = SearchResult(
        video_ids=video_ids,
        total=total,
        has_next=has_next,
        next_page=page + 1,
        facets=facets,
        query=q_str,
    )

    # --- Store the full result in cache ---
    cache.set(cache_key, search_result, timeout=SEARCH_CACHE_TTL)
    logger.debug("Cache SET search_videos — key=%s, ttl=%ss", cache_key, SEARCH_CACHE_TTL)

    return search_result


def _get_facets(client, q_str: str) -> Dict[str, List[FacetValue]]:
    """
    Computes facet counts using FT.AGGREGATE with GROUPBY.
    Returns up to 5 values per facet (same limit as V4 "size": 5).

    V4 facets: owner_full_name, type_title, disciplines_title, tags_name,
               channels_title, cursus, main_lang → all replicated here + themes.

    The 8 FT.AGGREGATE calls are expensive — results are cached in Redis (TTL=120s).
    """
    # --- Cache-aside: same pattern as V4 context_video_data() ---
    cache_key = _make_cache_key("facets", q_str)
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache HIT _get_facets — key=%s", cache_key)
        return cached

    facets: Dict[str, List[FacetValue]] = {}

    for redis_field, display_name in FACET_FIELDS:
        try:
            req = (
                AggregateRequest(q_str)
                .group_by(f"@{redis_field}", reducers.count().alias("count"))
                .sort_by(Desc("@count"))
                .limit(0, 5)
                .dialect(2)
            )
            agg_result = client.ft(search_settings.search_index_name).aggregate(req)

            buckets = []
            for row in agg_result.rows:
                row_dict = dict(zip(row[::2], row[1::2])) if row else {}
                value = row_dict.get(redis_field) or row_dict.get(f"@{redis_field}", "")
                count_str = row_dict.get("count", "0")
                if value:
                    buckets.append(FacetValue(value=value, count=int(count_str)))

            facets[display_name] = buckets

        except Exception as exc:
            logger.debug("Facet aggregation failed for field '%s': %s", redis_field, exc)
            facets[display_name] = []

    cache.set(cache_key, facets, timeout=FACETS_CACHE_TTL)
    logger.debug("Cache SET _get_facets — key=%s, ttl=%ss", cache_key, FACETS_CACHE_TTL)

    return facets
