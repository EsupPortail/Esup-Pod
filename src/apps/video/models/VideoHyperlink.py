"""
Esup-Pod - VideoHyperlink model.
Represents a clickable hyperlink overlay displayed on a video at a given time range.
"""

import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class VideoHyperlink(models.Model):
    """
    Esup-Pod - A hyperlink overlay associated with a video.
    Displays a clickable link (with optional icon and CSS position) between time_start and time_end.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="hyperlinks",
        verbose_name=_("Video"),
    )
    url = models.URLField(max_length=500, verbose_name=_("URL"), default="")
    text = models.CharField(max_length=255, verbose_name=_("Displayed text"), default="")
    icon = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Icon"))
    position = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Position (CSS)")
    )
    time_start = models.PositiveIntegerField(
        verbose_name=_("Start time (seconds)"), default=0
    )
    time_end = models.PositiveIntegerField(
        verbose_name=_("End time (seconds)"), default=0
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadata for the VideoHyperlink model."""

        verbose_name = _("Video Hyperlink")
        verbose_name_plural = _("Video Hyperlinks")
        ordering = ["time_start"]

    def __str__(self):
        return (
            f"{self.video.title} - {self.text} ({self.time_start}s -> {self.time_end}s)"
        )
