"""
Esup-Pod - Tests for completion settings.
"""

from django.test import TestCase

from src.apps.completion.apps import sync_roles
from src.apps.completion.conf import completion_settings
from src.apps.completion.models import Role


def test_completion_settings_loaded():
    """Test that completion settings are loaded correctly."""
    assert completion_settings.default_lang_track == "fr"
    assert isinstance(completion_settings.role_choices, list)


class CompletionRoleSyncTests(TestCase):
    """Tests for initializing database roles from completion settings."""

    def test_sync_roles_creates_configured_roles_idempotently(self):
        """Configured roles are created once with their labels and ordering."""
        sync_roles(sender=None)
        sync_roles(sender=None)

        for order, (code, label) in enumerate(completion_settings.role_choices):
            role = Role.objects.get(code=code)
            self.assertEqual(role.label, str(label))
            self.assertEqual(role.order, order)
