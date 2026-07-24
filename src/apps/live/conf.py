"""
Esup-Pod - Live configuration.

Typed and validated configuration for the live app using pydantic-settings.
"""

from typing import List, Tuple, Type

from django.utils.translation import gettext as _
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import live as defaults


class LiveConfig(BaseSettings):
    """Live app configuration with typed fields and validation."""

    # --- Feature Flags ---
    use_live: bool = Field(
        default=defaults.USE_LIVE,
        description=_("Enable the live streaming and events module globally."),
        json_schema_extra={"public": True},
    )
    use_live_transcription: bool = Field(
        default=defaults.USE_LIVE_TRANSCRIPTION,
        description=_("Enable real-time live transcription via Celery."),
        json_schema_extra={"public": True},
    )

    # --- Access Control ---
    affiliation_event: List[str] = Field(
        default=list(defaults.AFFILIATION_EVENT),
        description=_(
            "User affiliations allowed to create events (e.g. faculty, employee, staff)."
        ),
    )
    event_group_admin: str = Field(
        default=defaults.EVENT_GROUP_ADMIN,
        description=_("Django group name granting event management rights."),
    )

    # --- Timing ---
    heartbeat_delay: int = Field(
        default=defaults.HEARTBEAT_DELAY,
        description=_("Interval in seconds between viewer heartbeat pings."),
        json_schema_extra={"public": True},
    )

    # --- Thumbnails ---
    default_event_thumbnail: str = Field(
        default=defaults.DEFAULT_EVENT_THUMBNAIL,
        description=_("Relative path to the default event thumbnail."),
        json_schema_extra={"public": True},
    )
    default_thumbnail: str = Field(
        default=defaults.DEFAULT_THUMBNAIL,
        description=_("Relative path to the default building/broadcaster thumbnail."),
    )

    # --- Email ---
    email_on_event_scheduling: bool = Field(
        default=defaults.EMAIL_ON_EVENT_SCHEDULING,
        description=_("Send a confirmation email when an event is scheduled."),
    )

    # --- Transcription ---
    live_transcriptions_folder: str = Field(
        default=defaults.LIVE_TRANSCRIPTIONS_FOLDER,
        description=_("Subfolder inside MEDIA_ROOT for live VTT transcript files."),
    )

    # --- Recording ---
    default_event_path: str = Field(
        default=defaults.DEFAULT_EVENT_PATH,
        description=_(
            "Filesystem path where recorded event files are stored by the piloting service."
        ),
    )
    default_event_type_id: int = Field(
        default=defaults.DEFAULT_EVENT_TYPE_ID,
        description=_("Default Type ID assigned to events on creation."),
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


# Singleton instance
live_settings = LiveConfig()
