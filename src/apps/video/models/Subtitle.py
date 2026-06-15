"""
Esup-Pod - Video subtitle model.
"""

from django.db import models
from src.apps.encoding.services.storage import get_storage_path_transcript
from src.config.defaults import video as defaults
from .Video import Video


class Subtitle(models.Model):
    """
    Model representing a subtitle for a video.
    """

    video = models.ForeignKey(Video, related_name="subtitles", on_delete=models.CASCADE)
    language = models.CharField(
        max_length=10,
        choices=[(lang["value"], lang["label"]) for lang in defaults.SUBTITLE_LANGUAGES],
        default=defaults.DEFAULT_SUBTITLE_LANGUAGE,
    )
    file = models.FileField(upload_to=get_storage_path_transcript)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.video.title} - {self.language}"
