"""
Video configuration.

Typed and validated configuration for the video app using pydantic-settings.
"""

from typing import Tuple, Type


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
        description="Enable video statistics view.",
    )
    view_stats_auth: bool = Field(
        default=defaults.VIEW_STATS_AUTH,
        description="Require authentication to view statistics.",
    )
    user_video_category: bool = Field(
        default=defaults.USER_VIDEO_CATEGORY,
        description="Enable per-user video categories.",
    )
    webtv_mode: bool = Field(
        default=defaults.WEBTV_MODE,
        description="Enable WebTV mode (channel-based display).",
    )
    use_duplicate: bool = Field(
        default=defaults.USE_DUPLICATE,
        description="Enable video form duplication.",
    )
    use_cut: bool = Field(
        default=defaults.USE_CUT,
        description="Enable video cutting feature.",
    )
    allow_authenticated_upload: bool = Field(
        default=defaults.ALLOW_AUTHENTICATED_UPLOAD,
        description="Allow authenticated users to upload videos.",
    )

    # --- Licensing ---
    default_license: str = Field(
        default=defaults.DEFAULT_LICENSE,
        description="Default license for uploaded videos.",
    )
    channel_mode: bool = Field(
        default=defaults.CHANNEL_MODE,
        description="Display videos by thematic channels.",
    )

    # --- UI / Display Flags ---
    hide_user_filter: bool = Field(
        default=defaults.HIDE_USER_FILTER,
        description="Hide the user filter in the video list (RGPD).",
    )
    hide_tags: bool = Field(
        default=defaults.HIDE_TAGS, description="Hide tags in the video list."
    )
    force_lowercase_tags: bool = Field(
        default=defaults.FORCE_LOWERCASE_TAGS, description="Force tags to lowercase."
    )
    max_tag_length: int = Field(
        default=defaults.MAX_TAG_LENGTH, description="Maximum tag length."
    )
    number_tags_cloud: int = Field(
        default=defaults.NUMBER_TAGS_CLOUD, description="Number of tags in the cloud."
    )
    hide_share: bool = Field(
        default=defaults.HIDE_SHARE, description="Hide the share button."
    )
    hide_disciplines: bool = Field(
        default=defaults.HIDE_DISCIPLINES, description="Hide disciplines filter."
    )
    hide_cursus: bool = Field(
        default=defaults.HIDE_CURSUS, description="Hide cursus filter."
    )
    hide_types: bool = Field(
        default=defaults.HIDE_TYPES, description="Hide types filter."
    )
    restrict_edit_to_staff: bool = Field(
        default=defaults.RESTRICT_EDIT_TO_STAFF,
        description="Restrict video editing to staff users only.",
    )
    homepage_shows_passworded: bool = Field(
        default=defaults.HOMEPAGE_SHOWS_PASSWORDED,
        description="Show password-protected videos on the homepage.",
    )

    # --- Cache ---
    cache_timeout: int = Field(
        default=defaults.CACHE_TIMEOUT,
        description="Default cache timeout for video data in seconds.",
    )

    model_config = SettingsConfigDict(
        env_prefix="POD_VIDEO_",
        case_sensitive=False,
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
