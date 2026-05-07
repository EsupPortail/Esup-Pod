"""
Esup-Pod - Production configuration.

Secure settings for deployment: disables debug mode, enforces strict CORS policies,
and retrieves allowed hosts from environment variables.

Usage:
    export DJANGO_SETTINGS_MODULE=config.django.prod.prod
"""

from config.env import env

from ..base import *  # noqa: F401, F403

DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
