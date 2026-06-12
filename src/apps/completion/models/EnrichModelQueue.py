"""
Esup-Pod - EnrichModelQueue model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class EnrichModelQueue(models.Model):
    """
    Queue for background compilation/enrichment of transcription models (Kaldi/VOSK).
    """

    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="enrichment_queues",
        verbose_name=_("Video"),
    )
    track = models.ForeignKey(
        "video.Subtitle",
        on_delete=models.CASCADE,
        related_name="enrichment_queues",
        verbose_name=_("Track"),
    )
    added_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=(
            ("pending", _("Pending")),
            ("processing", _("Processing")),
            ("done", _("Done")),
            ("error", _("Error")),
        ),
        default="pending",
    )

    class Meta:
        """Meta options for EnrichModelQueue."""

        verbose_name = _("Enrich Model Queue")
        verbose_name_plural = _("Enrich Model Queues")

    def __str__(self):
        return f"Queue for {self.track} - {self.status}"
