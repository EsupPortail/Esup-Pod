from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class InteractiveConfig(AppConfig):
    name = 'interactive'
    trans_version = _('Interactive version')
    trans_name = _('Interactive')
    trans_original_name = _('interactive')
    trans_edit = _('Edit the interactive')
