"""
Esup-Pod - Overlay model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from src.apps.completion.conf import completion_settings


class Overlay(models.Model):
    """
    HTML Overlays displayed on top of the video player at specific timestamps.
    """

    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="overlays",
        verbose_name=_("Video"),
    )
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    time_start = models.PositiveIntegerField(verbose_name=_("Start time (seconds)"))
    time_end = models.PositiveIntegerField(verbose_name=_("End time (seconds)"))
    content = models.TextField(verbose_name=_("HTML Content"))

    class Meta:
        """Meta options for Overlay."""

        verbose_name = _("Overlay")
        verbose_name_plural = _("Overlays")
        permissions = [
            ("add_overlay_anywhere", _("Can add/manage overlays on ANY video")),
        ]

    def __str__(self):
        return f"{self.title} ({self.time_start}s - {self.time_end}s)"

    def clean(self):
        """
        Validates timestamps:
        - time_start < time_end
        - Overlays must not overlap for the same video.
        """
        super().clean()
        if self.time_start >= self.time_end:
            raise ValidationError(_("Start time must be strictly less than end time."))

        if self.video:
            # Check video duration if known
            if self.video.duration and self.time_end > self.video.duration:
                raise ValidationError(
                    _("End time cannot be greater than the video duration.")
                )

            # Check overlap
            overlapping = (
                Overlay.objects.filter(video=self.video)
                .filter(
                    time_start__lt=self.time_end,
                    time_end__gt=self.time_start,
                )
                .exclude(pk=self.pk)
            )
            if overlapping.exists():
                raise ValidationError(
                    _("This overlay overlaps with an existing overlay.")
                )

    def save(self, *args, **kwargs):
        """Save the overlay instance."""
        if completion_settings.link_superposition:
            # Implement auto-linking logic if needed (or do it in serializer)
            pass
        super().save(*args, **kwargs)
