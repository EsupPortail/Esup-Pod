"""
Local testing configuration.

Lightweight setup for running tests locally without Docker.
Uses an in-memory SQLite database by default for speed and allows all hosts.

Usage:
    export DJANGO_SETTINGS_MODULE=config.django.test.test
    pytest
"""

import os

from config.django.test.init_env import *  # noqa: F401, F403

from ..base import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("TEST_DB_NAME", ":memory:"),
    }
}

ALLOWED_HOSTS = ["*"]
