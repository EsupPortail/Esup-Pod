"""
Esup-Pod - VideoNote model.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class VideoNote(models.Model):
    """Represents a user note attached to a video, with an optional timestamp."""

    class PrivacyStatus(models.TextChoices):
        """Privacy level of the note."""

        PRIVATE = "private", _("Private (only me)")
        PUBLIC = "public", _("Public (everyone who can see the video)")

    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("Video"),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="video_notes",
        verbose_name=_("Owner"),
    )
    content = models.TextField(verbose_name=_("Content"))
    timestamp = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Timestamp (seconds)"),
        help_text=_("Video time in seconds. Leave empty for a global note."),
    )
    privacy = models.CharField(
        _("Privacy"),
        max_length=20,
        choices=PrivacyStatus.choices,
        default=PrivacyStatus.PRIVATE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """VideoNote model metadata."""

        verbose_name = _("Video Note")
        verbose_name_plural = _("Video Notes")
        ordering = ["timestamp", "created_at"]

    def __str__(self):
        ts = f" @{self.timestamp}s" if self.timestamp is not None else ""
        return f"{self.owner.username}{ts} — {self.content[:50]}"
