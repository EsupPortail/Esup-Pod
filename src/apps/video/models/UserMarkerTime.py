"""
Esup-Pod - User video marker time model.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserMarkerTime(models.Model):
    """
    Stores the last playback position for a user on a specific video.
    Allows resuming playback from the last watched position.
    """

    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="marker_times",
        verbose_name=_("Video"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marker_times",
        verbose_name=_("User"),
    )
    marker = models.PositiveIntegerField(
        _("Marker (seconds)"),
        default=0,
        help_text=_("Last playback position in seconds."),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """UserMarkerTime model metadata."""

        unique_together = [("video", "user")]
        verbose_name = _("User Marker Time")
        verbose_name_plural = _("User Marker Times")

    def __str__(self):
        return f"{self.user.username} @ {self.marker}s on '{self.video.title}'"
