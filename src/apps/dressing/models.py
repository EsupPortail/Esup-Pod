"""
Esup-Pod - Dressing models.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from src.apps.authentication.models.AccessGroup import AccessGroup
from src.apps.utils.models.CustomImageModel import CustomImageModel


class Dressing(models.Model):
    """
    Esup-Pod - Model representing a Video Dressing (Habillage).
    Provides configuration for adding watermarks and opening/ending credits to a video.
    """

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
            "of the content. (max length: 100 characters)"
        ),
    )

    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="owners_dressing",
        verbose_name=_("Owners"),
        blank=True,
    )

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
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
        "video.Video",
        verbose_name=_("Opening credits"),
        related_name="opening_credits",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    ending_credits = models.ForeignKey(
        "video.Video",
        verbose_name=_("Ending credits"),
        related_name="ending_credits",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    videos = models.ManyToManyField(
        "video.Video",
        related_name="videos_dressing",
        verbose_name=_("Videos"),
        blank=True,
    )

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Metadata for Dressing model."""

        verbose_name = _("Video dressing")
        verbose_name_plural = _("Video dressings")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def to_runner_parameters(self):
        """Returns the dictionary representation for esup-runner parameters."""
        data = {}
        if self.watermark and hasattr(self.watermark, "file") and self.watermark.file:
            # Assumes the storage backend will provide a valid download URL
            data["watermark"] = self.watermark.file.url
            data["watermark_position_orig"] = self.position
            data["watermark_opacity"] = str(self.opacity)

        if self.opening_credits and self.opening_credits.video_file:
            data["opening_credits_video"] = self.opening_credits.video_file.url
            if self.opening_credits.duration:
                data["opening_credits_video_duration"] = str(
                    self.opening_credits.duration
                )

        if self.ending_credits and self.ending_credits.video_file:
            data["ending_credits_video"] = self.ending_credits.video_file.url
            if self.ending_credits.duration:
                data["ending_credits_video_duration"] = str(self.ending_credits.duration)

        return data
