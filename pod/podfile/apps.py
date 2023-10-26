from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PodfileConfig(AppConfig):
    name = "pod.podfile"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Pod files")
