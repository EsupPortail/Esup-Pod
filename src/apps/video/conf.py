"""
Esup-Pod - Video configuration.

Typed and validated configuration for the video app using pydantic-settings.
"""

from typing import Tuple, Type, Dict
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import video as defaults


class VideoConfig(BaseSettings):
    """Esup-Pod - Video app configuration with typed fields and validation."""

    # --- Feature Flags ---
    use_stats_view: bool = Field(
        default=defaults.USE_STATS_VIEW,
        description="Enable video statistics view.",
        json_schema_extra={"public": True},
    )
    view_stats_auth: bool = Field(
        default=defaults.VIEW_STATS_AUTH,
        description="Require authentication to view statistics.",
        json_schema_extra={"public": True},
    )
    user_video_category: bool = Field(
        default=defaults.USER_VIDEO_CATEGORY,
        description="Enable per-user video categories.",
        json_schema_extra={"public": True},
    )
    webtv_mode: bool = Field(
        default=defaults.WEBTV_MODE,
        description="Enable WebTV mode (channel-based display).",
        json_schema_extra={"public": True},
    )
    use_duplicate: bool = Field(
        default=defaults.USE_DUPLICATE,
        description="Enable video form duplication.",
        json_schema_extra={"public": True},
    )
    use_cut: bool = Field(
        default=defaults.USE_CUT,
        description="Enable video cutting feature.",
        json_schema_extra={"public": True},
    )
    allow_authenticated_upload: bool = Field(
        default=defaults.ALLOW_AUTHENTICATED_UPLOAD,
        description="Allow authenticated users to upload videos.",
        json_schema_extra={"public": True},
    )
    active_video_comment: bool = Field(
        default=defaults.ACTIVE_VIDEO_COMMENT,
        description="Enable video commenting system.",
        json_schema_extra={"public": True},
    )

    # --- Licensing ---
    default_license: str = Field(
        default=defaults.DEFAULT_LICENSE,
        description="Default license for uploaded videos.",
        json_schema_extra={"public": True},
    )
    channel_mode: bool = Field(
        default=defaults.CHANNEL_MODE,
        description="Display videos by thematic channels.",
        json_schema_extra={"public": True},
    )

    # --- UI / Display Flags ---
    hide_user_filter: bool = Field(
        default=defaults.HIDE_USER_FILTER,
        description="Hide the user filter in the video list (RGPD).",
        json_schema_extra={"public": True},
    )
    hide_tags: bool = Field(
        default=defaults.HIDE_TAGS,
        description="Hide tags in the video list.",
        json_schema_extra={"public": True},
    )
    force_lowercase_tags: bool = Field(
        default=defaults.FORCE_LOWERCASE_TAGS,
        description="Force tags to lowercase.",
        json_schema_extra={"public": True},
    )
    max_tag_length: int = Field(
        default=defaults.MAX_TAG_LENGTH,
        description="Maximum tag length.",
        json_schema_extra={"public": True},
    )
    number_tags_cloud: int = Field(
        default=defaults.NUMBER_TAGS_CLOUD,
        description="Number of tags in the cloud.",
        json_schema_extra={"public": True},
    )
    hide_share: bool = Field(
        default=defaults.HIDE_SHARE,
        description="Hide the share button.",
        json_schema_extra={"public": True},
    )
    hide_disciplines: bool = Field(
        default=defaults.HIDE_DISCIPLINES,
        description="Hide disciplines filter.",
        json_schema_extra={"public": True},
    )
    hide_cursus: bool = Field(
        default=defaults.HIDE_CURSUS,
        description="Hide cursus filter.",
        json_schema_extra={"public": True},
    )
    hide_types: bool = Field(
        default=defaults.HIDE_TYPES,
        description="Hide types filter.",
        json_schema_extra={"public": True},
    )
    restrict_edit_to_staff: bool = Field(
        default=defaults.RESTRICT_EDIT_TO_STAFF,
        description="Restrict video editing to staff users only.",
        json_schema_extra={"public": True},
    )
    homepage_shows_passworded: bool = Field(
        default=defaults.HOMEPAGE_SHOWS_PASSWORDED,
        description="Show password-protected videos on the homepage.",
        json_schema_extra={"public": True},
    )

    # --- Cache ---
    cache_timeout: int = Field(
        default=defaults.CACHE_TIMEOUT,
        description="Default cache timeout for video data in seconds.",
    )

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    # --- Expiration Settings ---
    accommodation_years: Dict[str, int] = Field(
        default_factory=lambda: defaults.ACCOMMODATION_YEARS,
        description="Dictionary linking an affiliation to a number of years before expiration.",
    )
    default_year_date_delete: int = Field(
        default=defaults.DEFAULT_YEAR_DATE_DELETE,
        description="Default number of years before a video is deleted.",
    )

    # --- Metadata (Dublin Core) ---
    default_dc_coverage: str = Field(
        default=defaults.DEFAULT_DC_COVERAGE,
        description="Default Dublin Core coverage metadata.",
    )
    default_dc_rights: str = Field(
        default=defaults.DEFAULT_DC_RIGHTS,
        description="Default Dublin Core rights metadata.",
    )
    template_visible_settings: Dict[str, str] = Field(
        default=defaults.TEMPLATE_VISIBLE_SETTINGS,
        description="Global display settings (e.g. TITLE_ETB) for metadata.",
    )

    # --- Media Defaults ---
    default_thumbnail: str | None = Field(
        default=defaults.DEFAULT_THUMBNAIL,
        description="Path to the default video thumbnail.",
    )
    default_type_id: int = Field(
        default=defaults.DEFAULT_TYPE_ID,
        description="Default Type ID for new videos.",
    )

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
        """
        return (
            init_settings,
            env_settings,
            DjangoSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


# Singleton instance
video_settings = VideoConfig()
