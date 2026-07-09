"""
Esup-Pod - Notes configuration.
"""

from typing import Tuple, Type
from django.utils.translation import gettext as _
from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import notes as defaults


class NotesConfig(BaseSettings):
    """Esup-Pod - Notes app configuration."""

    use_notes: bool = Field(
        default=defaults.USE_NOTES,
        description=_("Enable video notes feature."),
        json_schema_extra={"public": True},
    )

    model_config = SettingsConfigDict(case_sensitive=False)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Add DjangoSettingsSource to priority list."""
        return (
            init_settings,
            env_settings,
            DjangoSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


notes_settings = NotesConfig()
