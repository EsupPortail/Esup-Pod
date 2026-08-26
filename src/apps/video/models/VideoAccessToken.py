"""
Esup-Pod - Video access token model.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class VideoAccessToken(models.Model):
    """
    A time-limited, revocable access token for sharing a video securely.
    Allows sharing videos (even password-protected ones) via a unique URL.
    """

    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="access_tokens",
        verbose_name=_("Video"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="video_access_tokens",
        verbose_name=_("Created By"),
    )
    token = models.UUIDField(
        _("Token"),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
    )
    label = models.CharField(
        _("Label"),
        max_length=100,
        blank=True,
        help_text=_(
            "Optional label to identify the purpose of this token "
            "(e.g. 'Shared with John')."
        ),
    )
    expires_at = models.DateTimeField(
        _("Expires At"),
        null=True,
        blank=True,
        help_text=_(
            "If set, the token becomes invalid after this date. "
            "Leave empty for no expiry."
        ),
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Deactivate this token to revoke access without deleting it."),
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    last_used_at = models.DateTimeField(
        _("Last Used At"),
        null=True,
        blank=True,
        help_text=_("Tracks last access for audit purposes."),
    )
    use_count = models.PositiveIntegerField(
        _("Use Count"),
        default=0,
        help_text=_("Number of times this token has been used to access the video."),
    )

    class Meta:
        """VideoAccessToken model metadata."""

        verbose_name = _("Video Access Token")
        verbose_name_plural = _("Video Access Tokens")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token for '{self.video.title}' by {self.created_by.username}"

    def is_valid(self) -> bool:
        """Returns True if the token is active and not expired."""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def record_use(self):
        """Updates usage tracking fields when the token is consumed."""
        self.last_used_at = timezone.now()
        self.use_count += 1
        self.save(update_fields=["last_used_at", "use_count"])
