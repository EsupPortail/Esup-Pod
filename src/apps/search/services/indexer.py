"""
Esup-Pod - Search indexer service.

Manages the Redis Search index lifecycle and video document indexing.
Equivalent to V4's pod/video_search/utils.py (create_index_es, index_es, delete_es).

Redis Search schema:
  - 12 TEXT fields (weighted, full-text searchable)
  - 12 TAG fields  (exact filters + 8 facets)
  - 3  NUMERIC SORTABLE fields (date ranges + sorting)
"""

import logging
from typing import Optional

import redis
from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.exceptions import ResponseError

from src.apps.search.conf import search_settings

logger = logging.getLogger(__name__)

# Redis client singleton (lazy init)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Returns a shared Redis client for Redis Search operations.
    Equivalent to Elasticsearch(ES_URL, ...) in V4.

    Uses SEARCH_REDIS_URL and SEARCH_REDIS_OPTIONS from SearchConfig.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            search_settings.search_redis_url,
            socket_timeout=search_settings.search_timeout,
            socket_connect_timeout=search_settings.search_timeout,
            retry_on_timeout=True,
            **search_settings.search_redis_options,
        )
    return _redis_client


def _build_schema() -> list:
    """
    Builds the Redis Search schema from SearchConfig weights.

    Full schema (derived from V4 search_template_fr.json + get_json_to_index()):

    TEXT fields (full-text, weighted):
      title, description, owner_full_name, owner_username,
      tags_text, type_title, disciplines_text, channels_text,
      themes_text, contributors_text, overlays_text, chapters_text

    TAG fields (exact filters + facets):
      type_slug, tags_slug, disciplines_slug, channels_slug, themes_slug,
      cursus_slug, main_lang, owner_username_tag,
      mediatype, is_restricted, has_password, site_id

    NUMERIC SORTABLE fields (ranges + sorting):
      date_added_ts, date_evt_ts, duration
    """
    s = search_settings
    return [
        # --- TEXT fields ---
        TextField("title", weight=s.search_weight_title),
        TextField("description", weight=s.search_weight_description),
        TextField("owner_full_name", weight=s.search_weight_owner),
        TextField("owner_username", weight=s.search_weight_owner_username),
        TextField("tags_text", weight=s.search_weight_tags),
        TextField("type_title", weight=s.search_weight_type),
        TextField("disciplines_text", weight=s.search_weight_disciplines),
        TextField("channels_text", weight=s.search_weight_channels),
        TextField("themes_text", weight=s.search_weight_themes),
        TextField("contributors_text", weight=s.search_weight_contributors),
        TextField("overlays_text", weight=s.search_weight_overlays),
        TextField("chapters_text", weight=s.search_weight_chapters),
        # --- TAG fields (facets + filters) ---
        TagField("type_slug"),
        TagField("tags_slug", separator=","),
        TagField("disciplines_slug", separator=","),
        TagField("channels_slug", separator=","),
        TagField("themes_slug", separator=","),
        TagField("cursus_slug"),
        TagField("main_lang"),
        TagField("owner_username_tag"),
        TagField("mediatype"),
        TagField("is_restricted"),
        TagField("has_password"),
        TagField("site_id", separator=","),
        # --- NUMERIC SORTABLE fields ---
        NumericField("date_added_ts", sortable=True),
        NumericField("date_evt_ts", sortable=True),
        NumericField("duration", sortable=True),
    ]


def create_index() -> bool:
    """
    Creates the Redis Search index.
    Equivalent to create_index_es() in V4.

    Returns True on success, False on failure.
    Skips silently if the index already exists.
    """
    client = get_redis_client()
    try:
        definition = IndexDefinition(
            prefix=[search_settings.search_key_prefix],
            index_type=IndexType.HASH,
        )
        client.ft(search_settings.search_index_name).create_index(
            _build_schema(),
            definition=definition,
        )
        logger.info(
            "Redis Search index '%s' created successfully.",
            search_settings.search_index_name,
        )
        return True
    except ResponseError as exc:
        if "Index already exists" in str(exc):
            logger.debug(
                "Redis Search index '%s' already exists, skipping creation.",
                search_settings.search_index_name,
            )
            return True
        logger.error(
            "Error creating Redis Search index '%s': %s",
            search_settings.search_index_name,
            exc,
        )
        return False


def drop_index() -> bool:
    """
    Deletes the Redis Search index (structure only, not the HASH data).
    Equivalent to delete_index_es() in V4.

    Returns True on success, False on failure.
    """
    client = get_redis_client()
    try:
        client.ft(search_settings.search_index_name).dropindex(delete_documents=False)
        logger.info(
            "Redis Search index '%s' dropped.",
            search_settings.search_index_name,
        )
        return True
    except ResponseError as exc:
        if "Unknown Index name" in str(exc):
            logger.debug(
                "Redis Search index '%s' does not exist, nothing to drop.",
                search_settings.search_index_name,
            )
            return True
        logger.error(
            "Error dropping Redis Search index '%s': %s",
            search_settings.search_index_name,
            exc,
        )
        return False


def drop_and_recreate_index() -> bool:
    """
    Drops then recreates the Redis Search index.
    Used by the reindex_videos --drop management command
    (equivalent to V4 create_pod_index command).
    """
    dropped = drop_index()
    if not dropped:
        logger.warning("Could not drop index, attempting creation anyway.")
    return create_index()


def _build_video_document(video) -> dict:  # noqa: C901
    """
    Builds the HASH document to store in Redis for a given video.
    Equivalent to Video.get_json_to_index() in V4.

    Covers all fields from the V4 schema + V5 additions
    (themes, contributors via Contribution model, overlays).
    """
    from datetime import date as date_type

    # --- Contributors (V5: Contribution model → contributor.full_name + role) ---
    contributors_names = []
    try:
        for contrib in video.contributions.select_related("contributor").all():
            contributors_names.append(contrib.contributor.full_name)
    except Exception:
        pass

    # --- Overlays (V5: Overlay model → title) ---
    overlays_titles = []
    try:
        overlays_titles = list(video.overlays.values_list("title", flat=True))
    except Exception:
        pass

    # --- Themes (V5: Theme model in collection → title + slug) ---
    themes_titles = []
    themes_slugs = []
    try:
        for theme in video.themes.all():
            themes_titles.append(theme.title)
            themes_slugs.append(theme.slug)
    except Exception:
        pass

    # --- Disciplines ---
    disciplines_titles = []
    disciplines_slugs = []
    try:
        for disc in video.disciplines.all():
            disciplines_titles.append(disc.title)
            disciplines_slugs.append(disc.slug)
    except Exception:
        pass

    # --- Tags ---
    tags_names = []
    tags_slugs = []
    try:
        for tag in video.tags.all():
            tags_names.append(tag.name)
            tags_slugs.append(tag.slug)
    except Exception:
        pass

    # --- Sites ---
    site_ids = []
    try:
        site_ids = [str(s.id) for s in video.sites.all()]
    except Exception:
        pass

    # --- Timestamps ---
    try:
        date_added_ts = int(video.created_at.timestamp())
    except Exception:
        date_added_ts = 0

    date_evt_ts = 0
    try:
        if video.date_of_event:
            if isinstance(video.date_of_event, date_type):
                from datetime import datetime

                date_evt_ts = int(
                    datetime.combine(video.date_of_event, datetime.min.time()).timestamp()
                )
    except Exception:
        pass

    # --- Channel ---
    channel_title = ""
    channel_slug = ""
    try:
        if video.channel:
            channel_title = video.channel.title
            channel_slug = video.channel.slug
    except Exception:
        pass

    return {
        # TEXT — full-text searchable
        "title": video.title or "",
        "description": video.description or "",
        "owner_full_name": video.owner.get_full_name() if video.owner else "",
        "owner_username": video.owner.username if video.owner else "",
        "tags_text": " ".join(tags_names),
        "type_title": video.type.title if video.type else "",
        "disciplines_text": " ".join(disciplines_titles),
        "channels_text": channel_title,
        "themes_text": " ".join(themes_titles),
        "contributors_text": " ".join(contributors_names),
        "overlays_text": " ".join(overlays_titles),
        "chapters_text": "",  # Reserved — chapters absent in V5
        # TAG — exact filters + facets
        "type_slug": video.type.slug if video.type else "",
        "tags_slug": ",".join(tags_slugs),
        "disciplines_slug": ",".join(disciplines_slugs),
        "channels_slug": channel_slug,
        "themes_slug": ",".join(themes_slugs),
        "cursus_slug": video.cursus.slug if video.cursus else "",
        "main_lang": video.language.slug if video.language else "",
        "owner_username_tag": video.owner.username if video.owner else "",
        "mediatype": "video" if getattr(video, "is_video", True) else "audio",
        "is_restricted": "1" if video.status == "RE" else "0",
        "has_password": "1" if video.password else "0",
        "site_id": ",".join(site_ids),
        # NUMERIC SORTABLE — ranges + sorting
        "date_added_ts": date_added_ts,
        "date_evt_ts": date_evt_ts,
        "duration": video.duration or 0,
        # Metadata (stored, not indexed by FT.SEARCH)
        "thumbnail_url": video.thumbnail_url or "",
        "full_url": video.get_absolute_url() or "",
        "slug": video.slug or "",
        "video_id": video.pk,
    }


def index_video(video) -> bool:
    """
    Indexes (or re-indexes) a single video in Redis Search.
    Equivalent to index_es(video) in V4.

    Stores the video as a Redis HASH at key: <prefix><id>
    """
    client = get_redis_client()
    try:
        key = f"{search_settings.search_key_prefix}{video.pk}"
        doc = _build_video_document(video)
        client.hset(key, mapping=doc)
        logger.debug("Video pk=%s indexed at key '%s'.", video.pk, key)
        return True
    except Exception as exc:
        logger.error("Error indexing video pk=%s: %s", video.pk, exc)
        return False


def index_video_by_id(video_id: int) -> bool:
    """
    Fetches a video by its PK and indexes it.
    Used by background signals and management commands.
    """
    from src.apps.video.models import Video

    try:
        video = Video.objects.select_related(
            "owner", "type", "cursus", "language", "channel"
        ).get(pk=video_id)
        return index_video(video)
    except Video.DoesNotExist:
        logger.warning("Video pk=%s not found, skipping index.", video_id)
        return False


def delete_video_from_index(video_id: int) -> bool:
    """
    Removes a video's HASH from Redis (and therefore from the index).
    Equivalent to delete_es(video_id) in V4.
    """
    client = get_redis_client()
    key = f"{search_settings.search_key_prefix}{video_id}"
    try:
        client.delete(key)
        logger.debug("Video pk=%s removed from index (key='%s').", video_id, key)
        return True
    except Exception as exc:
        logger.error("Error deleting video pk=%s from index: %s", video_id, exc)
        return False
