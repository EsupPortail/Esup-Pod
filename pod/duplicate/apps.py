from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DuplicateConfig(AppConfig):
    name = "pod.duplicate"
    verbose_name = _("Video duplicates")
