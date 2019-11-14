from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class EnrichmentConfig(AppConfig):
    name = 'enrichment'
    version = _('Enrichment version')
