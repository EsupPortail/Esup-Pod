"""
Esup-Pod - Import Video configuration.
"""

from typing import Tuple, Type
from django.utils.translation import gettext as _
from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import import_video as defaults


class ImportVideoConfig(BaseSettings):
    """Esup-Pod - Import Video app configuration."""

    use_import_video: bool = Field(
        default=defaults.USE_IMPORT_VIDEO,
        description=_("Enable external video import feature."),
        json_schema_extra={"public": True},
    )
    restrict_to_staff: bool = Field(
        default=defaults.RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY,
        description=_("Restrict video import to staff users only."),
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


import_video_settings = ImportVideoConfig()
