from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from pod.video.models import Video


class Favorite(models.Model):
    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    owner = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)
    date_added = models.DateTimeField(
        verbose_name=_("Date added"), default=timezone.now, editable=False
    )
    rank = models.IntegerField(verbose_name=_("Rank"), editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["video", "owner"], name="unique_favorite_video_owner"
            )
        ]
        ordering = ["id", "date_added"]
        verbose_name = _("Favorite")
        verbose_name_plural = _("Favorites")

    def __str__(self) -> str:
        """Display a favorite object as string."""
        return f"{self.video} - favorite - {self.owner}"
