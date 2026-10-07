"""
Esup-Pod - Search defaults.
Source of truth for default values for the Search app.

Replaces Elasticsearch with Redis Search (Redis 8).

V4 flag mapping:
  ES_URL          → SEARCH_REDIS_URL
  ES_INDEX        → SEARCH_INDEX_NAME
  ES_TIMEOUT      → SEARCH_TIMEOUT
  ES_MAX_RETRIES  → SEARCH_MAX_RETRIES
  ES_OPTIONS      → SEARCH_REDIS_OPTIONS
  ES_VERSION      → (obsolete, Redis Search is natively integrated)
"""

# =============================================================================
# Engine
# =============================================================================
# Selects the search backend.
# "redis"    → Redis Search (Redis 8, recommended)
# "database" → Native DB full-text search (minimal mode, no extra service)
# "disabled" → No search (endpoint returns empty results)
SEARCH_ENGINE = "redis"

# =============================================================================
# Redis Search connection  (equiv. ES_URL + ES_OPTIONS in V4)
# =============================================================================
# URL of the dedicated Redis Search instance.
# It is strongly recommended to use a SEPARATE Redis instance from the cache,
# session and Celery broker to avoid resource contention.
#
# Architecture:
#   Pod
#    ├── Redis cache       (DB 1, REDIS_CACHE_URL)
#    ├── Redis sessions    (DB 2, REDIS_SESSION_URL)
#    ├── Redis Celery      (DB 0, CELERY_BROKER_URL)
#    └── Redis Search      (dedicated, SEARCH_REDIS_URL)  ← this setting
SEARCH_REDIS_URL = "redis://redis-search:6379/0"

# Advanced connection options: SSL certificates, authentication, etc.
# Equivalent to ES_OPTIONS in V4.
# Example with SSL + basic auth:
#   SEARCH_REDIS_OPTIONS = {
#       "ssl": True,
#       "ssl_cert_reqs": "none",
#       "username": "default",
#       "password": "my-secret",
#   }
SEARCH_REDIS_OPTIONS = {}

# Maximum number of reconnection attempts on failure.
# Equivalent to ES_MAX_RETRIES in V4 (default was 10).
SEARCH_MAX_RETRIES = 3

# Connection timeout in seconds.
# Equivalent to ES_TIMEOUT in V4 (default was 30).
SEARCH_TIMEOUT = 5

# =============================================================================
# Index  (equiv. ES_INDEX in V4)
# =============================================================================
# Name of the Redis Search index. Equivalent to ES_INDEX in V4 ("pod").
SEARCH_INDEX_NAME = "pod_videos"

# Key prefix used for video HASH entries in Redis.
# Each indexed video is stored at: pod:video:<id>
SEARCH_KEY_PREFIX = "pod:video:"

# =============================================================================
# Pagination
# =============================================================================
# Default number of results per page (matches V4 page size = 12).
SEARCH_RESULTS_PER_PAGE = 12

# Minimum number of characters required before triggering a search query.
SEARCH_MIN_QUERY_LENGTH = 2

# Maximum page number allowed (same limit as V4 = 500 pages).
SEARCH_MAX_PAGE = 500

# =============================================================================
# Field weights for TEXT fields
# (derived from multi_match boost values in V4)
# =============================================================================
SEARCH_WEIGHT_TITLE = 2.0  # V4: title^1.1
SEARCH_WEIGHT_DESCRIPTION = 0.8  # V4: description^0.6
SEARCH_WEIGHT_OWNER = 1.0  # V4: owner_full_name^0.9
SEARCH_WEIGHT_OWNER_USERNAME = 0.9  # V4: owner^0.9
SEARCH_WEIGHT_TAGS = 1.5  # V4: tags.name^1.0 (boosted in V5)
SEARCH_WEIGHT_TYPE = 1.0  # V4: type.title^0.6 (boosted in V5)
SEARCH_WEIGHT_DISCIPLINES = 1.0  # V4: disciplines.title^0.6 (boosted in V5)
SEARCH_WEIGHT_CHANNELS = 0.8  # V4: channels.title^0.6
SEARCH_WEIGHT_THEMES = 0.5  # V4: themes.title^0.5
SEARCH_WEIGHT_CONTRIBUTORS = 0.6  # V4: contributors^0.6 (via Contribution model)
SEARCH_WEIGHT_OVERLAYS = 0.4  # V4: overlays.title^0.5 (slightly reduced)
SEARCH_WEIGHT_CHAPTERS = 0.4  # Reserved — chapters absent in V5, for future use

# =============================================================================
# Feature flags
# =============================================================================
# Expose 8 aggregation facets in search results (type, disciplines, channels,
# themes, tags, owner, cursus, lang). Equivalent to V4 "aggs" block.
SEARCH_ENABLE_FACETS = True

# Automatically re-index a Video via a post_save signal (like V4 behaviour).
# Set to False to only reindex via the `reindex_videos` management command.
SEARCH_ENABLE_AUTO_INDEX = True

# Auto-completion / suggestions (planned for a future version).
SEARCH_ENABLE_SUGGESTIONS = False
