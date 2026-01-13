from .dev import *  # noqa: F401, F403
from config.env import BASE_DIR

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
