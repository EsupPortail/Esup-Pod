"""
Esup-Pod - Search application configuration.
"""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    """Configuration for the search app."""

    name = "src.apps.search"
    label = "search"
    verbose_name = "Search"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """Connect signals on app startup."""
        import src.apps.search.signals  # noqa: F401
