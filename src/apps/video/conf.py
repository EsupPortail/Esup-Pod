"""
Esup-Pod - Video configuration.

Typed and validated configuration for the video app using pydantic-settings.
"""

from typing import Tuple, Type, Dict

from django.utils.translation import gettext as _
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import video as defaults


class VideoConfig(BaseSettings):
    """Video app configuration with typed fields and validation."""

    # --- Feature Flags ---
    use_stats_view: bool = Field(
        default=defaults.USE_STATS_VIEW,
        description=_("Enable video statistics view."),
        json_schema_extra={"public": True},
    )
    view_stats_auth: bool = Field(
        default=defaults.VIEW_STATS_AUTH,
        description=_("Require authentication to view statistics."),
        json_schema_extra={"public": True},
    )
    user_video_category: bool = Field(
        default=defaults.USER_VIDEO_CATEGORY,
        description=_("Enable per-user video categories."),
        json_schema_extra={"public": True},
    )
    webtv_mode: bool = Field(
        default=defaults.WEBTV_MODE,
        description=_("Enable WebTV mode (channel-based display)."),
        json_schema_extra={"public": True},
    )
    use_duplicate: bool = Field(
        default=defaults.USE_DUPLICATE,
        description=_("Enable video form duplication."),
        json_schema_extra={"public": True},
    )
    use_hyperlinks: bool = Field(
        default=defaults.USE_HYPERLINKS,
        description=_("Enable video hyperlinks."),
        json_schema_extra={"public": True},
    )
    use_video_access_token: bool = Field(
        default=defaults.USE_VIDEO_ACCESS_TOKEN,
        description=_("Enable secure video sharing via access tokens."),
        json_schema_extra={"public": True},
    )
    video_token_default_validity_days: int = Field(
        default=defaults.VIDEO_TOKEN_DEFAULT_VALIDITY_DAYS,
        description=_("Default token validity duration in days."),
    )
    video_token_max_validity_days: int = Field(
        default=defaults.VIDEO_TOKEN_MAX_VALIDITY_DAYS,
        description=_("Maximum allowed token validity in days."),
    )
    use_cut: bool = Field(
        default=defaults.USE_CUT,
        description=_("Enable video cutting feature."),
        json_schema_extra={"public": True},
    )
    allow_authenticated_upload: bool = Field(
        default=defaults.ALLOW_AUTHENTICATED_UPLOAD,
        description=_("Allow authenticated users to upload videos."),
        json_schema_extra={"public": True},
    )
    active_video_comment: bool = Field(
        default=defaults.ACTIVE_VIDEO_COMMENT,
        description=_("Enable video commenting system."),
        json_schema_extra={"public": True},
    )

    # --- Licensing ---
    default_license: str = Field(
        default=defaults.DEFAULT_LICENSE,
        description=_("Default license for uploaded videos."),
        json_schema_extra={"public": True},
    )
    channel_mode: bool = Field(
        default=defaults.CHANNEL_MODE,
        description=_("Display videos by thematic channels."),
        json_schema_extra={"public": True},
    )

    # --- UI / Display Flags ---
    hide_user_filter: bool = Field(
        default=defaults.HIDE_USER_FILTER,
        description=_("Hide the user filter in the video list (RGPD)."),
        json_schema_extra={"public": True},
    )
    hide_tags: bool = Field(
        default=defaults.HIDE_TAGS,
        description=_("Hide tags in the video list."),
        json_schema_extra={"public": True},
    )
    force_lowercase_tags: bool = Field(
        default=defaults.FORCE_LOWERCASE_TAGS,
        description=_("Force tags to lowercase."),
        json_schema_extra={"public": True},
    )
    max_tag_length: int = Field(
        default=defaults.MAX_TAG_LENGTH,
        description=_("Maximum tag length."),
        json_schema_extra={"public": True},
    )
    number_tags_cloud: int = Field(
        default=defaults.NUMBER_TAGS_CLOUD,
        description=_("Number of tags in the cloud."),
        json_schema_extra={"public": True},
    )
    hide_share: bool = Field(
        default=defaults.HIDE_SHARE,
        description=_("Hide the share button."),
        json_schema_extra={"public": True},
    )
    hide_disciplines: bool = Field(
        default=defaults.HIDE_DISCIPLINES,
        description=_("Hide disciplines filter."),
        json_schema_extra={"public": True},
    )
    hide_cursus: bool = Field(
        default=defaults.HIDE_CURSUS,
        description=_("Hide cursus filter."),
        json_schema_extra={"public": True},
    )
    hide_types: bool = Field(
        default=defaults.HIDE_TYPES,
        description=_("Hide types filter."),
        json_schema_extra={"public": True},
    )
    restrict_edit_to_staff: bool = Field(
        default=defaults.RESTRICT_EDIT_TO_STAFF,
        description=_("Restrict video editing to staff users only."),
        json_schema_extra={"public": True},
    )
    homepage_shows_passworded: bool = Field(
        default=defaults.HOMEPAGE_SHOWS_PASSWORDED,
        description=_("Show password-protected videos on the homepage."),
        json_schema_extra={"public": True},
    )

    # --- Cache ---
    cache_timeout: int = Field(
        default=defaults.CACHE_TIMEOUT,
        description=_("Default cache timeout for video data in seconds."),
    )

    site_url: str = Field(
        default="http://localhost:8000",
        description=_("Base URL of the site."),
    )

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    # --- Expiration Settings ---
    accommodation_years: Dict[str, int] = Field(
        default_factory=lambda: defaults.ACCOMMODATION_YEARS,
        description=_(
            "Dictionary linking an affiliation to a number of years before expiration."
        ),
    )
    default_year_date_delete: int = Field(
        default=defaults.DEFAULT_YEAR_DATE_DELETE,
        description=_("Default number of years before a video is deleted."),
    )
    delete_source_on_video_delete: bool = Field(
        default=defaults.DELETE_SOURCE_ON_VIDEO_DELETE,
        description=_("Delete the original source video file when a video is deleted."),
        json_schema_extra={"public": True},
    )

    # --- Metadata (Dublin Core) ---
    default_dc_coverage: str = Field(
        default=defaults.DEFAULT_DC_COVERAGE,
        description=_("Default Dublin Core coverage metadata."),
    )
    default_dc_rights: str = Field(
        default=defaults.DEFAULT_DC_RIGHTS,
        description=_("Default Dublin Core rights metadata."),
    )
    template_visible_settings: Dict[str, str] = Field(
        default=defaults.TEMPLATE_VISIBLE_SETTINGS,
        description=_("Global display settings (e.g. TITLE_ETB) for metadata."),
    )

    # --- Media Defaults ---
    default_thumbnail: str | None = Field(
        default=defaults.DEFAULT_THUMBNAIL,
        description=_("Path to the default video thumbnail."),
    )
    default_type_id: int = Field(
        default=defaults.DEFAULT_TYPE_ID,
        description=_("Default Type ID for new videos."),
    )

    # Note: We must use the `metadata_` prefix here. If we used `languages`,
    # pydantic's DjangoSettingsSource would automatically load Django's native
    # `LANGUAGES` setting (a list of tuples), crashing the db sync process.
    # The clean `languages` API is exposed via @property methods below.
    metadata_languages: list = Field(
        default_factory=lambda: defaults.METADATA_LANGUAGES,
        validation_alias="metadata_languages",
        description=_("Available languages for videos."),
        json_schema_extra={"public": True},
    )
    metadata_licenses: list = Field(
        default_factory=lambda: defaults.METADATA_LICENSES,
        validation_alias="metadata_licenses",
        description=_("Available content licenses."),
        json_schema_extra={"public": True},
    )
    metadata_cursus: list = Field(
        default_factory=lambda: defaults.METADATA_CURSUS,
        validation_alias="metadata_cursus",
        description=_("Available educational levels."),
        json_schema_extra={"public": True},
    )

    @property
    def languages(self) -> list:
        """Alias for metadata_languages."""
        return self.metadata_languages

    @property
    def licenses(self) -> list:
        """Alias for metadata_licenses."""
        return self.metadata_licenses

    @property
    def cursus(self) -> list:
        """Alias for metadata_cursus."""
        return self.metadata_cursus

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
