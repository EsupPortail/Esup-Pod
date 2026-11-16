"""
Esup-Pod - Chapter model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .Video import Video


class Chapter(models.Model):
    """Esup-Pod - A chapter marker of a video."""

    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="chapters",
        verbose_name=_("Video"),
    )
    title = models.CharField(_("Title"), max_length=100)
    time_start = models.PositiveIntegerField(
        _("Start time (seconds)"),
        default=0,
    )

    class Meta:
        """Configure chapter metadata and ordering."""

        verbose_name = _("Chapter")
        verbose_name_plural = _("Chapters")
        ordering = ["time_start"]
        unique_together = ("video", "title", "time_start")

    def __str__(self):
        return f"{self.video_id} - {self.title} ({self.time_start}s)"
