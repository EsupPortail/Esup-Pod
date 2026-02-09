"""
Configuration package initialization.

Attempts to import local setting overrides from `django.settings_local`.
This allows developers to apply machine-specific configurations (e.g., secrets,
debug flags) without modifying tracked files. If the module is missing,
it gracefully proceeds with default settings.
"""

try:
    from .django.settings_local import *  # noqa: F401, F403
except ImportError:
    pass
