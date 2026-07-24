"""
Esup-Pod - HeartBeat model.

Used to track active viewers during a live event.
Each anonymous or authenticated viewer is tracked by a unique viewkey.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class HeartBeat(models.Model):
    """
    Tracks individual viewer activity on a live Event.

    The frontend sends a periodic ping (every N seconds) with a unique
    viewkey. This allows counting concurrent viewers without requiring
    authentication.
    """

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        verbose_name=_("Viewer"),
        on_delete=models.CASCADE,
        related_name="heartbeats",
        help_text=_("Authenticated user associated with this heartbeat (optional)."),
    )
    viewkey = models.CharField(
        _("View key"),
        max_length=200,
        unique=True,
        help_text=_(
            "Unique client-side key identifying the browser session of the viewer."
        ),
    )
    event = models.ForeignKey(
        "Event",
        null=True,
        verbose_name=_("Event"),
        on_delete=models.CASCADE,
        related_name="heartbeats",
        help_text=_("The live event being watched."),
    )
    last_heartbeat = models.DateTimeField(
        _("Last heartbeat"),
        default=timezone.now,
        help_text=_("Timestamp of the most recent ping from this viewer."),
    )

    class Meta:
        """HeartBeat model metadata."""

        verbose_name = _("Heartbeat")
        verbose_name_plural = _("Heartbeats")
        ordering = ["event"]

    def __str__(self) -> str:
        user_str = self.user.username if self.user else "anonymous"
        return f"HeartBeat({user_str}, event={self.event_id})"

    @classmethod
    def cleanup_stale(cls, event, delay_seconds: int) -> None:
        """
        Remove heartbeats older than `delay_seconds` for a given event.
        Should be called before counting active viewers.
        """
        threshold = timezone.now() - timezone.timedelta(seconds=delay_seconds * 2)
        cls.objects.filter(event=event, last_heartbeat__lt=threshold).delete()
