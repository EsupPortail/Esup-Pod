import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _

from pod.video.models import Video

AI_ENRICHMENT_DIR = getattr(settings, "AI_ENRICHMENT_DIR", "ai-enrichments")


def get_storage_path_ai_enrichment(instance, filename):
    """Get the storage path for AI enrichment files."""
    fname, dot, extension = filename.rpartition(".")
    if extension.lower() not in ["json"]:
        raise ValidationError(_("Please choose a JSON file."))
    fname.index("/")
    return os.path.join(AI_ENRICHMENT_DIR, str(filename))


class AIEnrichment(models.Model):
    """AIEnrichment model."""

    class Meta:
        """Metadata class for AIEnrichment model."""

        ordering = ["-created_at"]
        get_latest_by = "updated_at"
        verbose_name = _("AI enrichment")
        verbose_name_plural = _("AI enrichments")

    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    ai_enrichment_file = models.FileField(
        verbose_name=_("AI enrichment file"),
        upload_to=get_storage_path_ai_enrichment,
        max_length=255,
        help_text=_("Please choose an AI enrichment file."),
        null=True,
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    is_ready = models.BooleanField(_("Is ready"), default=False)
    ai_enrichment_id_in_aristote = models.TextField(_("AI enrichment ID in Aristote"))
