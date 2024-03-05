"""Esup-Pod quiz app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QuizConfig(AppConfig):
    """Quiz config app."""

    name = "pod.quiz"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Quiz")
