"""
Esup-Pod - Video subtitle model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from src.apps.encoding.services.storage import get_storage_path_transcript
from .Video import Video


class Subtitle(models.Model):
    """
    Esup-Pod - Model representing a subtitle for a video.
    """

    class Language(models.TextChoices):
        """Supported languages for video subtitles."""

        FRENCH = "fr", _("French")
        ENGLISH = "en", _("English")
        SPANISH = "es", _("Spanish")

    video = models.ForeignKey(Video, related_name="subtitles", on_delete=models.CASCADE)
    language = models.CharField(
        max_length=10, choices=Language.choices, default=Language.FRENCH
    )
    file = models.FileField(upload_to=get_storage_path_transcript)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.video.title} - {self.language}"
