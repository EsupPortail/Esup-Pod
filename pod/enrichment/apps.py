from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EnrichmentConfig(AppConfig):
    name = 'enrichment'
    trans_version = _('Enrichment version')
    trans_name = _('Enrichment')
    trans_original_name = _('enrichment')
    trans_edit = _('Edit the enrichment')
