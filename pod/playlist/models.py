from typing import Iterable, Optional
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _

from pod.video.models import Video


class Playlist(models.Model):
    """Playlist model."""
    VISIBILITY_CHOICES = [
        ("public", _("Public")),
        ("protected", _("Protected")),
        ("private", _("Private"))
    ]
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=250,
        help_text=_("Please choose a name between 1 and 250 characters.")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        default="",
        help_text=_("Please choose a description. This description is empty by default.")
    )
    password = models.TextField(
        verbose_name=_("Password"),
        blank=True,
        default="",
        help_text=_("Please choose a password if this playlist is protected."),
    )
    visibility = models.CharField(
        verbose_name=_("Visibility"),
        max_length=9,
        choices=VISIBILITY_CHOICES,
        help_text=_("Please chosse an visibility among 'public', 'protected', 'private'.")
    )
    autoplay = models.BooleanField(
        verbose_name=_("Autoplay"),
        default=True,
        help_text=_("Please choose if this playlist is an autoplay playlist or not.")
    )
    slug = models.SlugField(
        _("slug"),
        unique=True,
        max_length=105,
        help_text=_(
            'Used to access this instance, the "slug" is a short'
            + " label containing only letters, numbers, underscore"
            + " or dash top."
        ),
        editable=False
    )
    owner = models.ForeignKey(User, verbose_name=_("User"), on_delete=models.CASCADE)

    date_created = models.DateTimeField(
        verbose_name=_("Date created"), default=timezone.now, editable=False
    )
    date_updated = models.DateTimeField(
        verbose_name=_("Date updated"), default=timezone.now, editable=False
    )

    class Meta:
        """Metadata for Playlist model."""

        ordering = ["name", "owner", "visibility", "date_updated"]
        get_latest_by = "date_updated"
        verbose_name = _("Playlist")
        verbose_name_plural = _("Playlists")

    def save(self) -> None:
        if self.visibility == "protected" and self.password == "" :
            raise ValueError("password cannot be empty when the visibility is 'protected'")

    def __str__(self) -> str:
        """Display a playlist as string."""
        return f"Name : {self.name} \
            - Description : {self.description} \
            - Visibility : {self.visibility} \
            - Autoplay : {self.autoplay} \
            - Slug : {self.slug} \
            - Owner : {self.owner}"


class PlaylistContent(models.Model):
    """PlaylistContent model."""

    playlist = models.ForeignKey(Playlist, verbose_name=_(
        "Playlist"), on_delete=models.CASCADE)
    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    date_added = models.DateTimeField(
        verbose_name=_("Date added"), default=timezone.now, editable=False
    )
    rank = models.IntegerField(verbose_name=_("Rank"), editable=False)

    class Meta:
        """Metadata for PlaylistContent model."""

        constraints = [
            # A video cannot be twice in a playlist.
            models.UniqueConstraint(
                fields=["playlist", "video"], name="unique_playlist_video"
            ),
            # A rank cannot be twice in a playlist.
            models.UniqueConstraint(
                fields=["playlist", "rank"], name="unique_playlist_rank"
            )
        ]

        ordering = ["playlist", "rank"]
        get_latest_by = "rank"
        verbose_name = _("Playlist content")
        verbose_name_plural = _("Playlist contents")

    def __str__(self) -> str:
        """Display a playlist content as string."""
        return f"Playlist : {self.playlist} - Video : {self.video} - Rank : {self.rank}"
