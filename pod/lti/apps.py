from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LtiConfig(AppConfig):
    name = "pod.lti"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("LTI provider")
