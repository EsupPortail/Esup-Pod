"""
Esup-Pod - Completion application configuration.
"""

from django.apps import AppConfig


class CompletionConfig(AppConfig):
    """
    Configuration for the completion app.
    """

    name = "src.apps.completion"
    label = "completion"
    verbose_name = "Completion Management"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """Connects signals and performs initialization on app startup."""
        pass
