"""
Esup-Pod - LiveTranscriptRunningTask model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from src.apps.live.models.Broadcaster import Broadcaster


class LiveTranscriptRunningTask(models.Model):
    """
    Tracks the Celery task ID for an ongoing live transcription,
    allowing the task to be revoked when the stream ends.
    """

    task_id = models.CharField(_("Task ID"), max_length=255, unique=True)
    broadcaster = models.ForeignKey(
        Broadcaster,
        verbose_name=_("Broadcaster"),
        help_text=_("Broadcaster name."),
        on_delete=models.CASCADE,
    )

    class Meta:
        """LiveTranscriptRunningTask model metadata."""

        verbose_name = _("Running task")
        verbose_name_plural = _("Running tasks")

    def __str__(self) -> str:
        return f"{self.broadcaster.name} - {self.task_id}"
