"""
Encoding configuration.

Typed and validated configuration for the encoding app using pydantic-settings.
"""

from typing import List, Tuple, Type


from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import encoding as defaults


class EncodingConfig(BaseSettings):
    """Encoding app configuration with typed fields and validation."""

    # --- Storage ---
    videos_dir: str = Field(
        default=defaults.VIDEOS_DIR,
        description="Default directory for video uploads.",
    )
    thumbnails_dir: str = Field(
        default=defaults.THUMBNAILS_DIR,
        description="Default directory for video thumbnails.",
    )

    # --- Upload ---
    max_upload_size_gb: int = Field(
        default=defaults.MAX_UPLOAD_SIZE_GB,
        description="Maximum video upload size in GB.",
    )
    allowed_extensions: Tuple[str, ...] = Field(
        default=defaults.ALLOWED_EXTENSIONS,
        description="Allowed video file extensions.",
    )
    video_required_fields: List[str] = Field(
        default=defaults.VIDEO_REQUIRED_FIELDS,
        description="List of required fields when uploading a video.",
    )

    # --- Quota / Licensing ---
    user_quota_size_gb: int = Field(
        default=defaults.USER_QUOTA_SIZE_GB,
        description="Max disk space per user in GB.",
    )

        # --- Encoding / FFmpeg ---
    ffmpeg_cmd: str = Field(
        default=defaults.FFMPEG_CMD, description="Path to ffmpeg binary."
    )
    ffprobe_cmd: str = Field(
        default=defaults.FFPROBE_CMD, description="Path to ffprobe binary."
    )
    ffmpeg_crf: int = Field(
        default=defaults.FFMPEG_CRF,
        description="FFmpeg CRF value (Constant Rate Factor). Lower = better quality.",
    )
    ffmpeg_nb_threads: str = Field(
        default=defaults.FFMPEG_NB_THREADS,
        description="FFmpeg encoding preset.",
    )
    ffprobe_get_info: str = Field(
        default=defaults.FFPROBE_GET_INFO,
        description="FFprobe info detail level.",
    )
    chunk_size: int = Field(
        default=defaults.CHUNK_SIZE,
        description="Chunk size for file operations.",
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
encoding_settings = EncodingConfig()

