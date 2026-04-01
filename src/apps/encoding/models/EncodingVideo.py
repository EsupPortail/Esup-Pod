"""
Esup-Pod - Encoding Video model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from src.apps.video.models import Video
from src.apps.encoding.services.storage import get_storage_path_encoded_video


class EncodingVideo(models.Model):
    """
    Esup-Pod - Model representing an encoded resolution of a video.
    """

    video = models.ForeignKey(
        Video,
        related_name="encodings",
        on_delete=models.CASCADE,
        verbose_name=_("Original Video"),
    )
    resolution = models.CharField(
        _("Resolution"), max_length=100, help_text=_("e.g. 360p, 720p, 1080p")
    )
    file = models.FileField(
        _("Encoded File"), upload_to=get_storage_path_encoded_video, max_length=255
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Esup-Pod - Meta class for EncodingVideo.
        """

        verbose_name = _("Encoded Video")
        verbose_name_plural = _("Encoded Videos")
        unique_together = ("video", "resolution")
        ordering = ["-resolution"]

    def __str__(self):
        return f"{self.video.title} - {self.resolution}"
