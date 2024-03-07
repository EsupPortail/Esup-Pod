from django.db import models
from django.utils.translation import ugettext as _

from pod.video.models import Video


class AIEnrichment(models.Model):
    """AIEnrichment model."""

    class Meta:
        """Metadata class for AIEnrichment model."""

        ordering = ["-created_at"]
        get_latest_by = "updated_at"
        verbose_name = _("AI enrichment")
        verbose_name_plural = _("AI enrichments")

    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    is_ready = models.BooleanField(_("Is ready"), default=False)
    ai_enrichment_id_in_aristote = models.TextField(_("AI enrichment ID in Aristote"))
