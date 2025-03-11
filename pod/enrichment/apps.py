from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EnrichmentConfig(AppConfig):
    name = "pod.enrichment"
    verbose_name = _("Enrichments")
    trans_version = _("Enrichment version")
    trans_name = _("Enrichment")
    trans_original_name = _("enrichment")
    trans_edit = _("Edit the enrichment")
    default_auto_field = "django.db.models.BigAutoField"
