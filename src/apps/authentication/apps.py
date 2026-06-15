"""
Esup-Pod - Authentication application configuration.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """
    Application configuration for the authentication module.
    """

    name = "src.apps.authentication"
    label = "authentication"
    verbose_name = "Authentication"
    default_auto_field = "django.db.models.AutoField"
