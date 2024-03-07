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

    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    is_ready = models.BooleanField(_("Is ready"), default=False)
    ai_enhancement_id_in_aristote = models.TextField(_("AI enhancement ID in Aristote"))
