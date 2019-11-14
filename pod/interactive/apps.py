from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class InteractiveConfig(AppConfig):
    name = 'interactive'
    version = _('Interactive version')
