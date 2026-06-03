"""
Esup-Pod - Video view count model.
"""

from datetime import date
from django.db import models
from src.apps.video.models import Video
from django.utils.translation import gettext_lazy as _


class ViewCount(models.Model):
    """
    Model representing the view count for a video on a specific date.
    """

    video = models.ForeignKey(Video, related_name="view_counts", on_delete=models.CASCADE)
    date = models.DateField(_("Date"), default=date.today)
    count = models.PositiveIntegerField(_("View Count"), default=0)

    class Meta:
        """ViewCount model metadata for reporting and uniques."""

        unique_together = ("video", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.video.title} - {self.date}: {self.count}"
