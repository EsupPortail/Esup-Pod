"""
Esup-Pod - Encoding application configuration.

Typed and validated configuration for the encoding app using pydantic-settings.
"""

from typing import List, Tuple, Type

from django.utils.translation import gettext as _


from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import encoding as defaults


class EncodingConfig(BaseSettings):
    """Encoding app configuration with typed fields and validation."""

    # --- Storage ---
    videos_dir: str = Field(
        default=defaults.VIDEOS_DIR,
        description=_("Default directory for video uploads."),
    )
    thumbnails_dir: str = Field(
        default=defaults.THUMBNAILS_DIR,
        description=_("Default directory for video thumbnails."),
    )

    # --- Upload ---
    max_upload_size_gb: int = Field(
        default=defaults.MAX_UPLOAD_SIZE_GB,
        description=_("Maximum video upload size in GB."),
        json_schema_extra={"public": True},
    )
    allowed_extensions: Tuple[str, ...] = Field(
        default=defaults.ALLOWED_EXTENSIONS,
        description=_("Allowed video file extensions."),
        json_schema_extra={"public": True},
    )
    video_required_fields: List[str] = Field(
        default=defaults.VIDEO_REQUIRED_FIELDS,
        description=_("List of required fields when uploading a video."),
        json_schema_extra={"public": True},
    )

    # --- Quota / Licensing ---
    user_quota_size_gb: int = Field(
        default=defaults.USER_QUOTA_SIZE_GB,
        description=_("Max disk space per user in GB."),
        json_schema_extra={"public": True},
    )

    keep_source_file: bool = Field(
        default=defaults.KEEP_SOURCE_FILE,
        description=_(
            "If True, the encoding webhook will not delete the original source video upon success."
        ),
    )
    site_url: str = Field(
        default="http://localhost:8000",
        description=_("Base URL of the site."),
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
            DjangoSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


# Singleton instance
encoding_settings = EncodingConfig()
