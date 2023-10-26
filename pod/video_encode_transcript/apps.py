from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VideoEncodeConfig(AppConfig):
    """Video encode configuration app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pod.video_encode_transcript"
    verbose_name = _("Video encoding and transcription")
