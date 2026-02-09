"""
Local development configuration (Non-Docker).

Lightweight setup to run directly on the host machine without containers.
Replaces MySQL with SQLite, Redis with local memory, and outputs emails to the console.

Usage:
    export DJANGO_SETTINGS_MODULE=config.django.dev.local
    python manage.py runserver
"""

from config.env import BASE_DIR

from .dev import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "TEST": {
            "NAME": BASE_DIR / "db_test.sqlite3",
        },
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "local-cache",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
