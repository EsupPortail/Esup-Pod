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
from django.utils.translation import gettext_lazy as _


class CollectionConfig(BaseSettings):
    """Collection app configuration with typed fields and validation."""

    # --- Channels ---
    use_channels: bool = Field(
        default=defaults.USE_CHANNELS,
        description=_("Enable/disable globally channel functionality."),
        json_schema_extra={"public": True},
    )
    owner_can_manage_channels: bool = Field(
        default=defaults.OWNER_CAN_MANAGE_CHANNELS,
        description=_("Allow video owners to manage their own channels."),
        json_schema_extra={"public": True},
    )
    user_can_create_channel: bool = Field(
        default=defaults.USER_CAN_CREATE_CHANNEL,
        description=_("Allow standard users to create channels."),
        json_schema_extra={"public": True},
    )
    can_change_channel_owner: bool = Field(
        default=defaults.CAN_CHANGE_CHANNEL_OWNER,
        description=_("Allow administrators to transfer channel ownership."),
        json_schema_extra={"public": True},
    )
    default_channel_image: str = Field(
        default=defaults.DEFAULT_CHANNEL_IMAGE,
        description=_("Default image for channels without logo."),
        json_schema_extra={"public": True},
    )
    default_channel_banner: str = Field(
        default=defaults.DEFAULT_CHANNEL_BANNER,
        description=_("Default banner for channels."),
        json_schema_extra={"public": True},
    )

    # --- Themes / Categories ---
    use_categories: bool = Field(
        default=defaults.USE_CATEGORIES,
        description=_("Enable/disable category/theme system."),
        json_schema_extra={"public": True},
    )
    theme_mandatory: bool = Field(
        default=defaults.THEME_MANDATORY,
        description=_("Make theme assignment mandatory when adding a video."),
        json_schema_extra={"public": True},
    )
    max_theme_depth: int = Field(
        default=defaults.MAX_THEME_DEPTH,
        description=_("Maximum depth of theme hierarchy."),
        json_schema_extra={"public": True},
    )
    show_empty_themes: bool = Field(
        default=defaults.SHOW_EMPTY_THEMES,
        description=_("Show themes even if they contain no videos."),
        json_schema_extra={"public": True},
    )
    owner_can_manage_themes: bool = Field(
        default=defaults.OWNER_CAN_MANAGE_THEMES,
        description=_(
            "Allow channel owners to create their own themes in their channels."
        ),
        json_schema_extra={"public": True},
    )

    # --- Playlists ---
    use_playlists: bool = Field(
        default=defaults.USE_PLAYLISTS,
        description=_("Enable/disable globally playlist module."),
        json_schema_extra={"public": True},
    )
    playlist_max_videos: int = Field(
        default=defaults.PLAYLIST_MAX_VIDEOS,
        description=_("Maximum number of videos in a single playlist."),
        json_schema_extra={"public": True},
    )
    allow_public_playlists: bool = Field(
        default=defaults.ALLOW_PUBLIC_PLAYLISTS,
        description=_("Allow users to make their playlists public."),
        json_schema_extra={"public": True},
    )

    # --- Favorites ---
    use_favorites: bool = Field(
        default=defaults.USE_FAVORITES,
        description=_("Enable favorites functionality."),
        json_schema_extra={"public": True},
    )

    # --- Visibility & Protection ---
    default_visibility: str = Field(
        default=defaults.DEFAULT_VISIBILITY,
        description=_("Default visibility for new collections."),
        json_schema_extra={"public": True},
    )
    use_password_protection: bool = Field(
        default=defaults.USE_PASSWORD_PROTECTION,
        description=_("Enable password protection for collections."),
        json_schema_extra={"public": True},
    )

    # --- General ---
    collections_per_page: int = Field(
        default=defaults.COLLECTIONS_PER_PAGE,
        description=_("Number of collections per page for pagination."),
        json_schema_extra={"public": True},
    )
    default_collection_order_field: str = Field(
        default=defaults.DEFAULT_COLLECTION_ORDER_FIELD,
        description=_("Default ordering field for collections."),
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
