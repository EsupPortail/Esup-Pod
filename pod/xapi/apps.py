"""Esup-Pod xAPI apps."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class XapiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pod.xapi"
    erbose_name = _("Esup-Pod xAPI")
