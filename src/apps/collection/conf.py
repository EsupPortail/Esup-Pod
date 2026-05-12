"""
Esup-Pod - Collection configuration.

Typed and validated configuration for the collection app using pydantic-settings.
"""

from typing import Tuple, Type
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import collection as defaults


class CollectionConfig(BaseSettings):
    """Esup-Pod - Collection app configuration with typed fields and validation."""

    # --- Channels ---
    use_channels: bool = Field(
        default=defaults.USE_CHANNELS,
        description="Enable/disable globally channel functionality.",
        json_schema_extra={"public": True},
    )
    owner_can_manage_channels: bool = Field(
        default=defaults.OWNER_CAN_MANAGE_CHANNELS,
        description="Allow video owners to manage their own channels.",
        json_schema_extra={"public": True},
    )
    user_can_create_channel: bool = Field(
        default=defaults.USER_CAN_CREATE_CHANNEL,
        description="Allow standard users to create channels.",
        json_schema_extra={"public": True},
    )
    can_change_channel_owner: bool = Field(
        default=defaults.CAN_CHANGE_CHANNEL_OWNER,
        description="Allow administrators to transfer channel ownership.",
        json_schema_extra={"public": True},
    )
    default_channel_image: str = Field(
        default=defaults.DEFAULT_CHANNEL_IMAGE,
        description="Default image for channels without logo.",
        json_schema_extra={"public": True},
    )
    default_channel_banner: str = Field(
        default=defaults.DEFAULT_CHANNEL_BANNER,
        description="Default banner for channels.",
        json_schema_extra={"public": True},
    )

    # --- Themes / Categories ---
    use_categories: bool = Field(
        default=defaults.USE_CATEGORIES,
        description="Enable/disable category/theme system.",
        json_schema_extra={"public": True},
    )
    theme_mandatory: bool = Field(
        default=defaults.THEME_MANDATORY,
        description="Make theme assignment mandatory when adding a video.",
        json_schema_extra={"public": True},
    )
    max_theme_depth: int = Field(
        default=defaults.MAX_THEME_DEPTH,
        description="Maximum depth of theme hierarchy.",
        json_schema_extra={"public": True},
    )
    show_empty_themes: bool = Field(
        default=defaults.SHOW_EMPTY_THEMES,
        description="Show themes even if they contain no videos.",
        json_schema_extra={"public": True},
    )
    owner_can_manage_themes: bool = Field(
        default=defaults.OWNER_CAN_MANAGE_THEMES,
        description="Allow channel owners to create their own themes in their channels.",
        json_schema_extra={"public": True},
    )

    # --- Playlists ---
    use_playlists: bool = Field(
        default=defaults.USE_PLAYLISTS,
        description="Enable/disable globally playlist module.",
        json_schema_extra={"public": True},
    )
    playlist_max_videos: int = Field(
        default=defaults.PLAYLIST_MAX_VIDEOS,
        description="Maximum number of videos in a single playlist.",
        json_schema_extra={"public": True},
    )
    allow_public_playlists: bool = Field(
        default=defaults.ALLOW_PUBLIC_PLAYLISTS,
        description="Allow users to make their playlists public.",
        json_schema_extra={"public": True},
    )

    # --- Favorites ---
    use_favorites: bool = Field(
        default=defaults.USE_FAVORITES,
        description="Enable favorites functionality.",
        json_schema_extra={"public": True},
    )

    # --- Visibility & Protection ---
    default_visibility: str = Field(
        default=defaults.DEFAULT_VISIBILITY,
        description="Default visibility for new collections.",
        json_schema_extra={"public": True},
    )
    use_password_protection: bool = Field(
        default=defaults.USE_PASSWORD_PROTECTION,
        description="Enable password protection for collections.",
        json_schema_extra={"public": True},
    )

    # --- General ---
    collections_per_page: int = Field(
        default=defaults.COLLECTIONS_PER_PAGE,
        description="Number of collections per page for pagination.",
        json_schema_extra={"public": True},
    )

    model_config = SettingsConfigDict(
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
collection_settings = CollectionConfig()
