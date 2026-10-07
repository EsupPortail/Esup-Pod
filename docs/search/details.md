# Search: Technical Details & Configuration

## Index Schema (Redis Search)

Each video is stored as a Redis **HASH** with the key `pod:video:<id>`.

### Indexed Fields

| Field                | Type      | Weight | Description                                      |
| :------------------- | :-------- | :----- | :----------------------------------------------- |
| `title`              | `TEXT`    | 2.0    | Video title (highest weight).                    |
| `description`        | `TEXT`    | 0.8    | Video description.                               |
| `owner_full_name`    | `TEXT`    | 1.0    | Owner's full name.                               |
| `owner_username`     | `TEXT`    | 0.9    | Owner's username.                                |
| `contributors`       | `TEXT`    | 0.6    | List of contributors (space-separated).           |
| `overlays_text`      | `TEXT`    | 0.4    | Text from video overlays.                        |
| `tags_name`          | `TEXT`    | 1.5    | Tag labels (full-text).                          |
| `type_slug`          | `TAG`     | —      | Video type slug (filter only).                   |
| `disciplines_slug`   | `TAG`     | —      | Discipline slugs (pipe-separated, filter only).  |
| `channels_slug`      | `TAG`     | —      | Channel slugs (filter only).                     |
| `themes_slug`        | `TAG`     | —      | Theme slugs (filter only).                       |
| `tags_slug`          | `TAG`     | —      | Tag slugs (filter only, for facets).             |
| `owner_username_tag` | `TAG`     | —      | Owner username (TAG for exact filter).           |
| `cursus_slug`        | `TAG`     | —      | Cursus slug (filter only).                       |
| `main_lang`          | `TAG`     | —      | Language code (filter only).                     |
| `mediatype`          | `TAG`     | —      | `"video"` or `"audio"`.                          |
| `site_id`            | `TAG`     | —      | Site identifier (multi-tenancy filter).           |
| `date_added_ts`      | `NUMERIC` | —      | Unix timestamp of `date_added` (sortable).        |
| `video_id`           | `NUMERIC` | —      | Primary key stored for retrieval.                |

> [!NOTE]
> `TEXT` fields are full-text searchable with weight-based scoring.
> `TAG` fields are used for exact filtering and facet aggregations.
> `NUMERIC` fields support range filters (`@date_added_ts:[ts1 ts2]`).

---

## Redis Cache Architecture

V5 uses Redis DB 1 (`REDIS_CACHE_URL`) as a **Django cache backend** (via `django-redis`).

### Cache Keys & TTL

| Key                            | Source                       | TTL    | Invalidated by              |
| :----------------------------- | :--------------------------- | :----- | :-------------------------- |
| `pod:search:results:<md5>`     | `search_videos()`            | 60s    | `post_save` / `post_delete` on `Video` |
| `pod:search:facets:<md5>`      | `_get_facets()`              | 120s   | `post_save` / `post_delete` on `Video` |
| `pod:video:metadata`           | `VideoViewSet.metadata()`    | 600s   | `post_save` / `post_delete` on `Video` |

The `<md5>` suffix is a hash of `"{q_str}:{page}"`, ensuring that each unique combination of filters and pagination has its own cache entry.

### Invalidation Flow

```text
Video.save() / Video.delete()
        │
        ▼
signals.invalidate_cache_on_video_save()
   / signals.invalidate_cache_on_video_delete()
        │
        ├── cache.delete_many(["pod:video:metadata"])
        └── cache.delete_pattern("pod:search:*")  ← requires django-redis
```

> [!IMPORTANT]
> `cache.delete_pattern()` requires the `django-redis` backend. If using the default `LocMemCache` (e.g. in tests), the call is silently ignored.

---

## Configuration Settings

All settings are defined in [`src/config/defaults/search.py`](../../src/config/defaults/search.py).
Override them by creating `src/config/settings/search.py` (see `.example` file).

### Engine

| Setting          | Default      | Description                                               |
| :--------------- | :----------- | :-------------------------------------------------------- |
| `SEARCH_ENGINE`  | `"redis"`    | `"redis"` / `"database"` / `"disabled"`                  |

### Redis Connection

| Setting                | Default                          | V4 Equivalent   |
| :--------------------- | :------------------------------- | :-------------- |
| `SEARCH_REDIS_URL`     | `"redis://redis-search:6379/0"`  | `ES_URL`        |
| `SEARCH_REDIS_OPTIONS` | `{}`                             | `ES_OPTIONS`    |
| `SEARCH_MAX_RETRIES`   | `3`                              | `ES_MAX_RETRIES`|
| `SEARCH_TIMEOUT`       | `5`                              | `ES_TIMEOUT`    |

> [!TIP]
> Use a **dedicated Redis instance** for Redis Search (separate from cache DB 1 and Celery DB 0) to avoid resource contention on large deployments.

### Index

| Setting              | Default          | Description                                  |
| :------------------- | :--------------- | :------------------------------------------- |
| `SEARCH_INDEX_NAME`  | `"pod_videos"`   | Name of the Redis Search index.              |
| `SEARCH_KEY_PREFIX`  | `"pod:video:"`   | Prefix for Hash keys in Redis.               |

### Pagination

| Setting                   | Default | Description                              |
| :------------------------ | :------ | :--------------------------------------- |
| `SEARCH_RESULTS_PER_PAGE` | `12`    | Number of results per page.              |
| `SEARCH_MIN_QUERY_LENGTH` | `2`     | Minimum characters to trigger FT.SEARCH. |
| `SEARCH_MAX_PAGE`         | `500`   | Maximum page number (0-indexed).          |

### Field Weights

Fine-tune ranking by adjusting these values in your `src/config/settings/search.py`:

```python
SEARCH_WEIGHT_TITLE        = 2.0   # V4: title^1.1
SEARCH_WEIGHT_DESCRIPTION  = 0.8   # V4: description^0.6
SEARCH_WEIGHT_TAGS         = 1.5   # V4: tags.name^1.0
SEARCH_WEIGHT_OWNER        = 1.0   # V4: owner_full_name^0.9
SEARCH_WEIGHT_CHANNELS     = 0.8   # V4: channels.title^0.6
SEARCH_WEIGHT_DISCIPLINES  = 1.0   # V4: disciplines.title^0.6
SEARCH_WEIGHT_THEMES       = 0.5   # V4: themes.title^0.5
SEARCH_WEIGHT_CONTRIBUTORS = 0.6   # V4: contributors^0.6
SEARCH_WEIGHT_OVERLAYS     = 0.4   # V4: overlays.title^0.5
```

### Feature Flags

| Setting                    | Default | Description                                                   |
| :------------------------- | :------ | :------------------------------------------------------------ |
| `SEARCH_ENABLE_FACETS`     | `True`  | Include facet aggregations in search responses.               |
| `SEARCH_ENABLE_AUTO_INDEX` | `True`  | Re-index videos automatically on `post_save`.                 |
| `SEARCH_ENABLE_SUGGESTIONS`| `False` | Auto-completion (planned for a future version).               |

---

## Code Map

| File                                                                 | Role                                                  |
| :------------------------------------------------------------------- | :---------------------------------------------------- |
| [`services/indexer.py`](../../src/apps/search/services/indexer.py)  | Redis client, index creation, single-video indexing.  |
| [`services/query.py`](../../src/apps/search/services/query.py)      | Query builder, `search_videos()`, `_get_facets()`, cache logic. |
| [`views/SearchViewSet.py`](../../src/apps/search/views/SearchViewSet.py) | DRF ViewSet exposing `/api/search/`.              |
| [`conf.py`](../../src/apps/search/conf.py)                          | `search_settings` — typed settings access via Pydantic.|
| [`management/commands/reindex_videos.py`](../../src/apps/search/management/commands/reindex_videos.py) | Bulk reindex command. |
| [`management/commands/warm_cache.py`](../../src/apps/search/management/commands/warm_cache.py) | Cache preloading command (equiv. V4 `cache_video_data`). |
| [`video/signals.py`](../../src/apps/video/signals.py)               | Cache invalidation on `Video` save/delete.            |

---

## Deployment Notes

### Docker Compose (Recommended)

```yaml
services:
  redis:
    image: redis:7-alpine
    # DB 0: Celery, DB 1: Django cache, DB 2: Sessions

  redis-search:
    image: redis/redis-stack-server:latest  # Redis 8 with Search module
    # DB 0: Search index
```

### Environment Variables (`.env`)

```bash
REDIS_CACHE_URL=redis://redis:6379/1        # Django cache (DB 1)
REDIS_SESSION_URL=redis://redis:6379/2      # Sessions (DB 2)
CELERY_BROKER_URL=redis://redis:6379/0      # Celery (DB 0)
CACHE_TIMEOUT=600                           # Default cache TTL (seconds)
```

In `src/config/settings/search.py`:

```python
SEARCH_ENGINE    = "redis"
SEARCH_REDIS_URL = "redis://redis-search:6379/0"
```

### First-time Setup

After deploying, run:

```bash
# 1. Create the Redis Search index and index all published videos
python manage.py reindex_videos

# 2. Pre-load the Django cache (DB 1) with static metadata
python manage.py warm_cache
```

---

## Further Reading

- ⬅️ **[Search Overview](README.md)**
- ⬅️ **[Back to Index](../README.md)**
