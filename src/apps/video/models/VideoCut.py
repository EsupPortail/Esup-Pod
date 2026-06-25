"""
Esup-Pod - VideoCut model.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class VideoCut(models.Model):
    """Stores the cut parameters (start/end in seconds) for a video."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.OneToOneField(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="cut",
        verbose_name=_("Video"),
    )
    time_start = models.PositiveIntegerField(verbose_name=_("Start (seconds)"))
    time_end = models.PositiveIntegerField(verbose_name=_("End (seconds)"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """VideoCut model metadata."""

        verbose_name = _("Video Cut")
        verbose_name_plural = _("Video Cuts")

    def __str__(self):
        return f"Cut for {self.video.title} ({self.time_start}s - {self.time_end}s)"
