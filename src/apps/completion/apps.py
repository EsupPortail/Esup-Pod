"""
Esup-Pod - Completion application configuration.
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def sync_roles(sender, **kwargs):
    """Create configured contributor roles after the completion tables exist."""
    from src.apps.completion.conf import completion_settings
    from src.apps.completion.models import Role

    for order, (code, label) in enumerate(completion_settings.role_choices):
        Role.objects.get_or_create(
            code=code,
            defaults={"label": str(label), "order": order},
        )


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
        post_migrate.connect(sync_roles, sender=self)
