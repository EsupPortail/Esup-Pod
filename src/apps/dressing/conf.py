"""
Esup-Pod - Dressing configuration.

Typed and validated configuration for the dressing app using pydantic-settings.
"""

from typing import Tuple, Type

from django.utils.translation import gettext_lazy as _
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import dressing as defaults


class DressingConfig(BaseSettings):
    """Esup-Pod - Dressing app configuration with typed fields and validation."""

    use_dressing: bool = Field(
        default=defaults.USE_DRESSING,
        description=_("Enable video dressing (watermark and credits)."),
        json_schema_extra={"public": True},
    )

    allow_user_custom_dressing: bool = Field(
        default=defaults.ALLOW_USER_CUSTOM_DRESSING,
        description=_("Allow standard users to create custom video dressings."),
        json_schema_extra={"public": True},
    )

    max_watermark_size_mb: int = Field(
        default=defaults.MAX_WATERMARK_SIZE_MB,
        description=_("Maximum size (in MB) for custom watermark images."),
        json_schema_extra={"public": True},
    )

    max_credits_duration_seconds: int = Field(
        default=defaults.MAX_CREDITS_DURATION_SECONDS,
        description=_(
            "Maximum duration (in seconds) allowed for opening/ending credits."
        ),
        json_schema_extra={"public": True},
    )

    default_watermark_opacity: int = Field(
        default=defaults.DEFAULT_WATERMARK_OPACITY,
        description=_("Default opacity for new watermarks (1-100)."),
        json_schema_extra={"public": True},
    )

    default_watermark_position: str = Field(
        default=defaults.DEFAULT_WATERMARK_POSITION,
        description=_("Default position for new watermarks."),
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
        """Customise settings sources to prioritize Django settings."""
        return (
            init_settings,
            env_settings,
            DjangoSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


# Singleton instance
dressing_settings = DressingConfig()
