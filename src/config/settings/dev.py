from .base import *
import os

DEBUG = True  
CORS_ALLOW_ALL_ORIGINS = True  

# Uncomment for debugging 
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "pod": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Detect MySQL configuration
HAS_MYSQL_CONFIG = all([
    os.getenv("MYSQL_HOST"),
    os.getenv("MYSQL_DATABASE"),
    os.getenv("MYSQL_USER"),
    os.getenv("MYSQL_PASSWORD"),
    os.getenv("MYSQL_PORT"),
])

USE_DOCKER = HAS_MYSQL_CONFIG

if not HAS_MYSQL_CONFIG:
    print("MySQL configuration incomplete or missing -> falling back to SQLite")

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
            "LOCATION": "unique-snowflake",
        }
    }

    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

else:
    print(f"MySQL configuration detected in your environement parameters (Host: {os.getenv('MYSQL_HOST')})")
