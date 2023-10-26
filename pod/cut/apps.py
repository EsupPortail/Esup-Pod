from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CutConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pod.cut"
    verbose_name = _("Video cuts")
