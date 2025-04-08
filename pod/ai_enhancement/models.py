from django.db import models
from django.utils.translation import gettext as _
from django.dispatch import receiver
from django.db.models.signals import post_save
from pod.video.models import Video


class AIEnhancement(models.Model):
    """AIEnhancement model."""

    class Meta:
        """Metadata class for AIEnhancement model."""

        ordering = ["-created_at"]
        get_latest_by = "updated_at"
        verbose_name = _("AI enhancement")
        verbose_name_plural = _("AI enhancements")

    video = models.OneToOneField(
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

    @property
    def sites(self) -> models.QuerySet:
        """Return the sites of the video."""
        return self.video.sites

    def __str__(self) -> str:
        """Return the string representation of the AI enhancement."""
        return f"{self.video.title} - {self.ai_enhancement_id_in_aristote}"


@receiver(post_save, sender=Video)
def delete_AIEnhancement(sender, instance, created, **kwargs):
    """
    Delete AIEnhancement if launch encoding if requested.

    Args:
        sender (:class:`pod.video.models.Video`): Video model class.
        instance (:class:`pod.video.models.Video`): Video object instance.
    """
    if hasattr(instance, "launch_encode") and instance.launch_encode is True:
        AIEnhancement.objects.filter(video=instance).delete()
