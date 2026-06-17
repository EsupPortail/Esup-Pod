"""
Esup-Pod - Contribution model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from src.apps.completion.conf import completion_settings


class Contribution(models.Model):
    """
    Links a Contributor to a Video with a specific role.
    Fusions V4 Contributor (when attached to video) and JobVideo.
    """

    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="contributions",
        verbose_name=_("Video"),
    )
    contributor = models.ForeignKey(
        "completion.Contributor",
        on_delete=models.CASCADE,
        related_name="contributions",
        verbose_name=_("Contributor"),
    )
    role = models.CharField(
        max_length=200,
        choices=completion_settings.role_choices,
        default="author",
        verbose_name=_("Role"),
    )
    job_title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Job title"),
        help_text=_("Only used if role is 'speaker'"),
    )

    class Meta:
        """Meta options for Contribution."""

        verbose_name = _("Contribution")
        verbose_name_plural = _("Contributions")
        unique_together = ("video", "contributor", "role")
        permissions = [
            ("add_contribution_anywhere", _("Can add/manage contributions on ANY video")),
        ]

    def __str__(self):
        return f"{self.contributor} - {self.get_role_display()} on {self.video}"

    def clean(self):
        """
        Validate that the same person does not have the same role twice on the same video.
        (unique_together handles this at DB level, clean handles it at form/serializer level)
        """
        super().clean()
        if (
            Contribution.objects.filter(
                video=self.video, contributor=self.contributor, role=self.role
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                _("This contributor already has this role on this video.")
            )
