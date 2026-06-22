"""
Esup-Pod - Tests for completion settings.
"""

from src.apps.completion.conf import completion_settings


def test_completion_settings_loaded():
    """Test that completion settings are loaded correctly."""
    assert completion_settings.default_lang_track == "fr"
    assert isinstance(completion_settings.role_choices, list)
