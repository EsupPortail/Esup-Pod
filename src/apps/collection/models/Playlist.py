"""
Esup-Pod - Playlist model.
"""

from django.db import models
from django.db.models import Max
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, identify_hasher
from src.apps.collection.models.base import BaseContainer
from src.apps.video.models.Video import Video


class Playlist(BaseContainer):
    """
    Model representing an ordered list of videos.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_playlists",
        verbose_name=_("Owner"),
    )
    is_public = models.BooleanField(
        _("Is Public"),
        default=True,
        help_text=_("If unchecked, the playlist is private."),
    )
    password = models.CharField(
        _("Password"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("Optional password for access protection."),
    )
    videos = models.ManyToManyField(
        Video,
        through="PlaylistItem",
        related_name="playlists",
        verbose_name=_("Videos"),
        blank=True,
    )

    class Meta(BaseContainer.Meta):
        """Playlist model metadata."""

        verbose_name = _("Playlist")
        verbose_name_plural = _("Playlists")

    def set_password(self) -> None:
        """Encrypts the password if provided."""
        if self.password:
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)

    def save(self, *args, **kwargs):
        """Handle password encryption before saving."""
        self.set_password()
        super().save(*args, **kwargs)


class PlaylistItem(models.Model):
    """
    Join table between Playlist and Video with ordering.
    """

    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="items")
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="playlist_links"
    )
    position = models.PositiveIntegerField(
        _("Position"),
        default=0,
        help_text=_("Order position of the video in the playlist."),
    )
    added_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Auto-calculate position if not provided."""
        if not self.position or self.position == 0:
            max_pos = PlaylistItem.objects.filter(playlist=self.playlist).aggregate(
                Max("position")
            )["position__max"]
            self.position = (max_pos or 0) + 1
        super().save(*args, **kwargs)

    class Meta:
        """PlaylistItem model metadata."""

        verbose_name = _("Playlist Item")
        verbose_name_plural = _("Playlist Items")
        unique_together = ("playlist", "video")
        ordering = ["position", "-added_at"]
