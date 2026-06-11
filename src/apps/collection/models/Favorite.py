"""
Esup-Pod - Favorite collection model.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from src.apps.video.models.Video import Video


class Favorite(models.Model):
    """
    Simple Model for marking a video as favorite.
    Personal list of videos per user.

    Note: Although functionally a "collection" of videos, this model does
    NOT inherit from BaseContainer. It acts purely as a Many-to-Many mapping
    between User and Video. Inheriting from BaseContainer would create
    unnecessary DB columns (title, slug, description) for every single 'like'.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorites",
        verbose_name=_("User"),
    )
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="favorited_by",
        verbose_name=_("Video"),
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Favorite model metadata."""

        verbose_name = _("Favorite")
        verbose_name_plural = _("Favorites")
        unique_together = ("user", "video")
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username}'s favorite: {self.video.title}"
