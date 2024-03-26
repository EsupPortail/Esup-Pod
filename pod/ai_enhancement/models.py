from django.db import models
from django.utils.translation import ugettext as _

from pod.video.models import Video


class AIEnhancement(models.Model):
    """AIEnhancement model."""

    class Meta:
        """Metadata class for AIEnhancement model."""

        ordering = ["-created_at"]
        get_latest_by = "updated_at"
        verbose_name = _("AI enhancement")
        verbose_name_plural = _("AI enhancements")

    video = models.ForeignKey(
        Video,
        verbose_name=_("Video"),
        on_delete=models.CASCADE,
        help_text=_("Select the video to enhance with AI"),
    )
    created_at = models.DateTimeField(
        verbose_name=_("Created at"),
        auto_now_add=True,
        help_text=_("The date and time when the enhancement was created"),
    )
    updated_at = models.DateTimeField(
        verbose_name=_("Updated at"),
        auto_now=True,
        help_text=_("The date and time when the enhancement was updated"),
    )
    is_ready = models.BooleanField(
        verbose_name=_("Is ready"),
        default=False,
        help_text=_("Check if the enhancement is ready"),
    )
    ai_enhancement_id_in_aristote = models.TextField(
        verbose_name=_("AI enhancement ID in Aristote"),
        help_text=_("Enter the ID of the enhancement in Aristote"),
    )
