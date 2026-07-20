"""
Esup-Pod - Completion configuration.

Typed and validated configuration for the completion app using pydantic-settings.
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
from src.config.defaults import completion as defaults


class CompletionConfig(BaseSettings):
    """Completion app configuration with typed fields and validation."""

    # Contributor roles
    role_choices: list = Field(
        default_factory=lambda: list(defaults.ROLE_CHOICES),
        description=_("Available roles for contributors."),
    )

    # Track kinds
    kind_choices: list = Field(
        default_factory=lambda: list(defaults.KIND_CHOICES),
        description=_("Available kinds for subtitle tracks."),
    )

    default_lang_track: str = Field(
        default=defaults.DEFAULT_LANG_TRACK,
        description=_("Default language for new subtitle tracks."),
    )

    link_superposition: bool = Field(
        default=defaults.LINK_SUPERPOSITION,
        description=_("Enable automatic conversion of URLs into links in overlays."),
    )

    use_speaker: bool = Field(
        default=defaults.USE_SPEAKER,
        description=_("Enable or disable the Speakers module."),
    )

    required_speaker_firstname: bool = Field(
        default=defaults.REQUIRED_SPEAKER_FIRSTNAME,
        description=_("Make the first name of a speaker mandatory."),
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
completion_settings = CompletionConfig()
