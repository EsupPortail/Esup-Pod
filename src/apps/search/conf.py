"""
Esup-Pod - Search configuration.

Typed and validated configuration for the search app using pydantic-settings.
Replaces Elasticsearch with Redis Search (Redis 8).
"""

from typing import Any, Dict, Tuple, Type

from django.utils.translation import gettext as _
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import search as defaults


class SearchConfig(BaseSettings):
    """
    Search app configuration with typed fields and validation.

    All settings can be overridden via:
      1. Django settings (src/config/settings/search.py)
      2. Environment variables
      3. .env file

    V4 Elasticsearch flag equivalents:
      ES_URL          → search_redis_url
      ES_INDEX        → search_index_name
      ES_TIMEOUT      → search_timeout
      ES_MAX_RETRIES  → search_max_retries
      ES_OPTIONS      → search_redis_options
    """

    # =========================================================================
    # Engine
    # =========================================================================
    search_engine: str = Field(
        default=defaults.SEARCH_ENGINE,
        description=_("Search engine backend. One of: 'redis', 'database', 'disabled'."),
    )

    # =========================================================================
    # Redis Search connection  (equiv. ES_URL + ES_OPTIONS in V4)
    # =========================================================================
    search_redis_url: str = Field(
        default=defaults.SEARCH_REDIS_URL,
        description=_(
            "URL of the dedicated Redis Search instance "
            "(equiv. ES_URL in V4). "
            "Recommended: use a separate Redis instance from cache/sessions/Celery."
        ),
    )
    search_redis_options: Dict[str, Any] = Field(
        default_factory=lambda: defaults.SEARCH_REDIS_OPTIONS,
        description=_(
            "Advanced Redis connection options: SSL, auth, etc. "
            "(equiv. ES_OPTIONS in V4). "
            "Example: {'ssl': True, 'password': 'secret'}"
        ),
    )
    search_max_retries: int = Field(
        default=defaults.SEARCH_MAX_RETRIES,
        description=_(
            "Maximum number of reconnection attempts on failure "
            "(equiv. ES_MAX_RETRIES in V4, was 10)."
        ),
    )
    search_timeout: int = Field(
        default=defaults.SEARCH_TIMEOUT,
        description=_(
            "Connection timeout in seconds " "(equiv. ES_TIMEOUT in V4, was 30)."
        ),
    )

    # =========================================================================
    # Index  (equiv. ES_INDEX in V4)
    # =========================================================================
    search_index_name: str = Field(
        default=defaults.SEARCH_INDEX_NAME,
        description=_(
            "Name of the Redis Search index (equiv. ES_INDEX in V4, was 'pod')."
        ),
    )
    search_key_prefix: str = Field(
        default=defaults.SEARCH_KEY_PREFIX,
        description=_(
            "Key prefix for video HASH entries in Redis. "
            "Each video is stored at: <prefix><id>."
        ),
    )

    # =========================================================================
    # Pagination
    # =========================================================================
    search_results_per_page: int = Field(
        default=defaults.SEARCH_RESULTS_PER_PAGE,
        description=_("Default number of results per page (V4 default was 12)."),
        json_schema_extra={"public": True},
    )
    search_min_query_length: int = Field(
        default=defaults.SEARCH_MIN_QUERY_LENGTH,
        description=_("Minimum number of characters required to trigger a search."),
        json_schema_extra={"public": True},
    )
    search_max_page: int = Field(
        default=defaults.SEARCH_MAX_PAGE,
        description=_("Maximum page number allowed (same limit as V4 = 500)."),
        json_schema_extra={"public": True},
    )

    # =========================================================================
    # Field weights for TEXT fields
    # (derived from multi_match boost values in V4)
    # =========================================================================
    search_weight_title: float = Field(
        default=defaults.SEARCH_WEIGHT_TITLE,
        description=_("TEXT weight for title field (V4: title^1.1)."),
    )
    search_weight_description: float = Field(
        default=defaults.SEARCH_WEIGHT_DESCRIPTION,
        description=_("TEXT weight for description field (V4: description^0.6)."),
    )
    search_weight_owner: float = Field(
        default=defaults.SEARCH_WEIGHT_OWNER,
        description=_("TEXT weight for owner full name field (V4: owner_full_name^0.9)."),
    )
    search_weight_owner_username: float = Field(
        default=defaults.SEARCH_WEIGHT_OWNER_USERNAME,
        description=_("TEXT weight for owner username field (V4: owner^0.9)."),
    )
    search_weight_tags: float = Field(
        default=defaults.SEARCH_WEIGHT_TAGS,
        description=_("TEXT weight for tags field (V4: tags.name^1.0)."),
    )
    search_weight_type: float = Field(
        default=defaults.SEARCH_WEIGHT_TYPE,
        description=_("TEXT weight for type title field (V4: type.title^0.6)."),
    )
    search_weight_disciplines: float = Field(
        default=defaults.SEARCH_WEIGHT_DISCIPLINES,
        description=_("TEXT weight for disciplines field (V4: disciplines.title^0.6)."),
    )
    search_weight_channels: float = Field(
        default=defaults.SEARCH_WEIGHT_CHANNELS,
        description=_("TEXT weight for channels field (V4: channels.title^0.6)."),
    )
    search_weight_themes: float = Field(
        default=defaults.SEARCH_WEIGHT_THEMES,
        description=_("TEXT weight for themes field (V4: themes.title^0.5)."),
    )
    search_weight_contributors: float = Field(
        default=defaults.SEARCH_WEIGHT_CONTRIBUTORS,
        description=_(
            "TEXT weight for contributors field "
            "(V4: contributors^0.6, V5: via Contribution model)."
        ),
    )
    search_weight_overlays: float = Field(
        default=defaults.SEARCH_WEIGHT_OVERLAYS,
        description=_(
            "TEXT weight for overlays field "
            "(V4: overlays.title^0.5, V5: via Overlay model)."
        ),
    )
    search_weight_chapters: float = Field(
        default=defaults.SEARCH_WEIGHT_CHAPTERS,
        description=_(
            "TEXT weight for chapters field "
            "(reserved — chapters are absent in V5, kept for future compatibility)."
        ),
    )

    # =========================================================================
    # Feature flags
    # =========================================================================
    search_enable_facets: bool = Field(
        default=defaults.SEARCH_ENABLE_FACETS,
        description=_(
            "Expose aggregation facets in search results "
            "(type, disciplines, channels, themes, tags, owner, cursus, lang). "
            "Equivalent to V4 'aggs' block."
        ),
        json_schema_extra={"public": True},
    )
    search_enable_auto_index: bool = Field(
        default=defaults.SEARCH_ENABLE_AUTO_INDEX,
        description=_(
            "Automatically re-index a video on post_save signal "
            "(like V4 behaviour). Set to False to only index via "
            "the 'reindex_videos' management command."
        ),
    )
    search_enable_suggestions: bool = Field(
        default=defaults.SEARCH_ENABLE_SUGGESTIONS,
        description=_(
            "Enable auto-completion suggestions (planned for a future version)."
        ),
        json_schema_extra={"public": True},
    )

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    @property
    def is_redis(self) -> bool:
        """Returns True if the Redis Search backend is active."""
        return self.search_engine == "redis"

    @property
    def is_disabled(self) -> bool:
        """Returns True if search is disabled."""
        return self.search_engine == "disabled"

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """
        Add DjangoSettingsSource to priority list.
        Priority (highest → lowest):
          1. init_settings     (programmatic overrides)
          2. env_settings      (environment variables)
          3. DjangoSettingsSource  (src/config/settings/search.py)
          4. dotenv_settings   (.env file)
          5. file_secret_settings
        """
        return (
            init_settings,
            env_settings,
            DjangoSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


# Singleton instance used across the application
search_settings = SearchConfig()
