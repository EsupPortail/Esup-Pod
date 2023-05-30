"""Esup-Pod favorite video model."""
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from pod.video.models import Video


class Favorite(models.Model):
    """Favorite video model."""

    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    owner = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    date_added = models.DateTimeField(
        verbose_name=_("Date added"), default=timezone.now, editable=False
    )
    rank = models.IntegerField(verbose_name=_("Rank"), editable=False)

    class Meta:
        """Metadata for favorite video Model."""

        constraints = [
            # A video can only be favorited once per owner
            models.UniqueConstraint(
                fields=["video", "owner"], name="unique_favorite_video_owner"
            ),
            # There mustn't be duplicated ranks for one owner
            models.UniqueConstraint(
                fields=["owner", "rank"], name="unique_favorite_owner_rank"
            ),
        ]
        # Default ordering for Favorites items (not for Favorite video list)
        ordering = ["owner", "rank"]
        # Latest by ascending rank.
        get_latest_by = "rank"
        verbose_name = _("Favorite video")
        verbose_name_plural = _("Favorite videos")

    def __str__(self) -> str:
        """Display a favorite object as string."""
        return f"{self.owner} - favorite {self.rank} - {self.video}"
