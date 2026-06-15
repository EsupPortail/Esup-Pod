"""
Esup-Pod - Encoding Video model.
"""

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from src.apps.video.models import Video
from src.apps.encoding.services.storage import get_storage_path_encoded_video
from src.apps.utils.files import safe_remove_file


class EncodingVideo(models.Model):
    """
    Model representing an encoded resolution of a video.
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
        Meta class for EncodingVideo.
        """

        verbose_name = _("Encoded Video")
        verbose_name_plural = _("Encoded Videos")
        unique_together = ("video", "resolution")
        ordering = ["-resolution"]

    def __str__(self):
        return f"{self.video.title} - {self.resolution}"


@receiver(post_delete, sender=EncodingVideo)
def auto_delete_encoded_file_on_delete(sender, instance, **kwargs):
    """
    Deletes physical encoded video files from disk when EncodingVideo object is deleted.
    """
    safe_remove_file(instance.file)
