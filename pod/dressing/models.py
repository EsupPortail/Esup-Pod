"""Esup-Pod dressing models."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from django.contrib.auth.models import User
from pod.authentication.models import AccessGroup
from pod.podfile.models import CustomImageModel
from django.utils.translation import ugettext_lazy as _
from pod.video.models import Video


class Dressing(models.Model):
    """Class describing Dressing objects."""

    TOP_RIGHT = "top_right"
    TOP_LEFT = "top_left"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_LEFT = "bottom_left"
    POSITIONS = (
        (TOP_RIGHT, _("Top right")),
        (TOP_LEFT, _("Top left")),
        (BOTTOM_RIGHT, _("Bottom right")),
        (BOTTOM_LEFT, _("Bottom left")),
    )

    title = models.CharField(
        _("Title"),
        max_length=100,
        unique=True,
        help_text=_(
            "Please choose a title as short and accurate as "
            "possible, reflecting the main subject / context "
            "of the content.(max length: 100 characters)"
        ),
    )

    owners = models.ManyToManyField(
        User,
        related_name="owners_dressing",
        verbose_name=_("Owners"),
        blank=True,
    )

    users = models.ManyToManyField(
        User,
        related_name="users_dressing",
        verbose_name=_("Users"),
        blank=True,
    )

    allow_to_groups = models.ManyToManyField(
        AccessGroup,
        blank=True,
        verbose_name=_("Groups"),
        help_text=_(
            "Select one or more groups who can manage and use this video dressing."
        ),
    )

    watermark = models.ForeignKey(
        CustomImageModel,
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Watermark"),
    )

    position = models.CharField(
        verbose_name=_("Position"),
        max_length=200,
        choices=POSITIONS,
        default=TOP_RIGHT,
        blank=True,
        null=True,
    )

    opacity = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        blank=True,
        null=True,
        verbose_name=_("Opacity"),
    )

    opening_credits = models.ForeignKey(
        Video,
        verbose_name=_("Opening credits"),
        related_name="opening_credits",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    ending_credits = models.ForeignKey(
        Video,
        verbose_name=_("Ending credits"),
        related_name="ending_credits",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    videos = models.ManyToManyField(
        Video,
        related_name="videos_dressing",
        verbose_name=_("Videos"),
        blank=True,
    )

    class Meta:
        """Metadata for Dressing model."""

        verbose_name = _("Video dressing")
        verbose_name_plural = _("Video dressings")

    def to_json(self):
        """Convert to json format for encoding logs"""
        return {
            "id": self.id,
            "title": self.title,
            "owners": list(self.owners.values_list("id", flat=True)),
            "users": list(self.users.values_list("id", flat=True)),
            "allow_to_groups": list(self.allow_to_groups.values_list("id", flat=True)),
            "watermark": self.watermark.file.url if self.watermark else None,
            "position": self.get_position_display(),
            "opacity": self.opacity,
            "opening_credits": self.opening_credits.slug
            if self.opening_credits
            else None,
            "ending_credits": self.ending_credits.slug if self.ending_credits else None,
        }
