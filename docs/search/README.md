# Search: Overview

The **Search** application provides full-text video search for Pod V5. It replaces the Elasticsearch-based backend of V4 with **Redis Search** (Redis 8), using the same Redis instance as the cache and session backend.

## Architecture

```text
Client (Frontend)
       │
       ▼
GET /api/search/?q=...
       │
       ▼
SearchViewSet.list()
       │
       ├── cache.get("pod:search:results:<md5>")  ← Redis DB 1 (HIT → skip Redis Search)
       │
       ├── search_videos(filters)               ← Redis Search (FT.SEARCH)
       │        │
       │        └── _get_facets(client, q_str)  ← 8× FT.AGGREGATE (cached 120s)
       │
       └── Video.objects.filter(pk__in=...)     ← MySQL / PostgreSQL (ordered by Redis result)
```

## V4 → V5 Migration

| V4 (Elasticsearch)       | V5 (Redis Search)              |
| :------------------------ | :----------------------------- |
| `ES_URL`                  | `SEARCH_REDIS_URL`             |
| `ES_INDEX`                | `SEARCH_INDEX_NAME`            |
| `ES_TIMEOUT`              | `SEARCH_TIMEOUT`               |
| `ES_MAX_RETRIES`          | `SEARCH_MAX_RETRIES`           |
| `ES_OPTIONS`              | `SEARCH_REDIS_OPTIONS`         |
| `"match_all": {}`         | `*` (Redis Search wildcard)    |
| `"aggs"` block            | `FT.AGGREGATE` per facet field |

## Key Features

| Feature                    | Description                                                                                       |
| :------------------------- | :------------------------------------------------------------------------------------------------ |
| **Full-text search**       | Searches `title`, `description`, `tags`, `contributors`, `overlays`, with configurable weights.   |
| **Faceted aggregations**   | Returns up to 5 buckets per facet: `type`, `disciplines`, `channels`, `themes`, `tags`, `owner`, `cursus`, `lang`. |
| **Redis cache layer**      | Results cached 60s, facets cached 120s in Redis DB 1. Automatic invalidation on video save/delete. |
| **Multi-site support**     | Queries are scoped to the current `site_id`.                                                      |
| **Pagination**             | 0-indexed pages, configurable page size, max 500 pages.                                           |
| **Engine fallback**        | `SEARCH_ENGINE=database` → basic Django ORM search (no Redis needed). `SEARCH_ENGINE=disabled` → always empty. |
| **Auto-reindex**           | On `Video.post_save`, the index is automatically updated (`SEARCH_ENABLE_AUTO_INDEX=True`).        |

## Redis Cache Strategy

The search app uses **two Redis databases** for different purposes:

| Redis DB | Role                      | Variable           | TTL    |
| :------- | :------------------------ | :----------------- | :----- |
| **DB 1** | Django cache (results, facets, metadata) | `REDIS_CACHE_URL`  | 60–600s |
| **Dedicated** | Redis Search index (FT.SEARCH / FT.AGGREGATE) | `SEARCH_REDIS_URL` | persistent |

Cache keys:
- `pod:search:results:<md5>` — Full search results (TTL: 60s)
- `pod:search:facets:<md5>` — Facet aggregations (TTL: 120s)
- `pod:video:metadata` — Video metadata endpoint (TTL: 600s)

All search caches are invalidated automatically via Django signals when any `Video` is saved or deleted.

## API Endpoints

| Method  | Endpoint       | Description                                      |
| :------ | :------------- | :----------------------------------------------- |
| **GET** | `/api/search/` | Full-text search with filters, pagination, facets. |

### Query Parameters

| Parameter    | Type     | Description                                          |
| :----------- | :------- | :--------------------------------------------------- |
| `q`          | `string` | Full-text search query.                              |
| `type`       | `string` | Filter by video type slug.                           |
| `discipline` | `string` | Filter by discipline slug (multi-value = OR).        |
| `channel`    | `string` | Filter by channel slug (multi-value = OR).           |
| `theme`      | `string` | Filter by theme slug (multi-value = OR).             |
| `tag`        | `string` | Filter by tag slug (multi-value = OR).               |
| `owner`      | `string` | Filter by owner username.                            |
| `cursus`     | `string` | Filter by cursus slug.                               |
| `lang`       | `string` | Filter by main language code (e.g. `fr`).            |
| `mediatype`  | `string` | `"video"` or `"audio"`.                              |
| `date_from`  | `int`    | Unix timestamp — lower bound on `date_added`.        |
| `date_to`    | `int`    | Unix timestamp — upper bound on `date_added`.        |
| `page`       | `int`    | Page number (0-indexed, max 500).                    |

### Response Format

```json
{
  "count": 42,
  "results": [ { "id": 1, "title": "..." }, "..." ],
  "facets": {
    "type":        [{ "value": "cours", "count": 12 }],
    "disciplines": [{ "value": "informatique", "count": 8 }],
    "channels":    [],
    "themes":      [],
    "tags":        [{ "value": "python", "count": 5 }],
    "owner":       [{ "value": "jdupont", "count": 3 }],
    "cursus":      [],
    "lang":        [{ "value": "fr", "count": 30 }]
  },
  "has_next": true,
  "next_page": 1,
  "query": "python"
}
```

## Management Commands

### `reindex_videos`

Re-indexes all published videos into Redis Search.

```bash
python manage.py reindex_videos
python manage.py reindex_videos --batch-size 200
python manage.py reindex_videos --drop  # Drop and recreate the index first
```

### `warm_cache` *(New in V5)*

Pre-loads the Redis cache (DB 1) with static video metadata. Equivalent of V4's `cache_video_data` command.

```bash
python manage.py warm_cache           # Clear stale cache + preload
python manage.py warm_cache --clear-only  # Clear only, no preload
```

> [!TIP]
> Add `warm_cache` to your cron to keep the cache warm:
> ```
> */10 * * * * python manage.py warm_cache
> ```

## Further Reading

- ➡️ **[Technical Details & Configuration](details.md)**: Index schema, field weights, connection settings, and advanced tuning.
- ⬅️ **[Back to Index](../README.md)**
