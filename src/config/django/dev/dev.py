"""
Esup-Pod - Development settings.

Configures the environment for local development, including debug mode and enhanced logging.
"""

import logging
import os
import re

import sqlparse

from ..base import *  # noqa: F401, F403

DEBUG = True
SHOW_SQL_QUERIES = False
CORS_ALLOW_ALL_ORIGINS = True
ALLOWED_HOSTS = ["*"]

# Service identifier label in logs (injected by docker-compose)
SERVICE_LABEL = os.environ.get("SERVICE_LABEL", "app").upper()


class ColoredFormatter(logging.Formatter):
    """
    Logging formatter with ANSI colors for service-based prefixes and log levels.
    """

    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    cyan = "\x1b[36;1m"
    magenta = "\x1b[35;1m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    # Per-service colors for prefix
    SERVICE_COLORS = {
        "API": "\x1b[36;1m",  # Bold Cyan
        "CELERY": "\x1b[35;1m",  # Bold Magenta
    }

    LEVEL_COLORS = {
        logging.DEBUG: blue,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def format(self, record):
        """Processes and colors the log message based on service label and level."""
        color = self.LEVEL_COLORS.get(record.levelno, self.grey)
        record.levelname = f"{color}{record.levelname:<8}{self.reset}"

        if record.name == "django.server":
            match = re.search(r'"\s(\d{3})\s', record.msg)
            if match:
                code = int(match.group(1))
                code_color = (
                    self.green
                    if code < 400
                    else (self.yellow if code < 500 else self.red)
                )
                record.msg = record.msg.replace(
                    str(code), f"{code_color}{code}{self.reset}"
                )

        # Replace verbose logger names with short prefixes
        if record.name == "django.db.backends":
            record.name = "[DB]"
        elif record.name == "django.server":
            record.name = "[HTTP]"
        elif record.name.startswith("celery"):
            record.name = "[CELERY]"
        elif record.name.startswith("django"):
            record.name = "[DJANGO]"
        elif record.name.startswith("src") or record.name.startswith("pod"):
            record.name = "[APP]"

        # Colored service prefix
        service = SERVICE_LABEL
        service_color = self.SERVICE_COLORS.get(service, self.grey)
        record.service = f"{service_color}[{service}]{self.reset}"

        formatted_msg = super().format(record)

        if record.name == "[DB]" and sqlparse and "SELECT" in formatted_msg:
            formatted_msg = sqlparse.format(
                formatted_msg, reindent=True, keyword_case="upper"
            )
            formatted_msg = f"{self.grey}{formatted_msg}{self.reset}"

        return formatted_msg


# --- FILTERS ---
class SkipIgnorableRequests(logging.Filter):
    """
    Logging filter to skip noisy requests (static files, favicon, etc.).
    """

    def filter(self, record):
        """Determines if a log record should be kept based on ignorable patterns."""
        msg = record.getMessage()
        if "/static/" in msg or "/media/" in msg:
            return False

        ignored_patterns = [
            "GET /serviceworker.js",
            "GET /favicon.ico",
            "GET /manifest.json",
            "apple-touch-icon",
            "/serviceworker.js",
        ]
        if any(pattern in msg for pattern in ignored_patterns):
            return False

        return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": ColoredFormatter,
            "format": "%(service)s %(levelname)s %(asctime)s %(name)-10s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "filters": {
        "skip_ignorable": {
            "()": SkipIgnorableRequests,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "level": "DEBUG",
            "filters": ["skip_ignorable"],
        },
    },
    "loggers": {
        # --- Django ---
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.utils.autoreload": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        # --- Celery ---
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "celery.app.trace": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # --- Application ---
        "pod": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "src": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

if SHOW_SQL_QUERIES:
    LOGGING["loggers"]["django.db.backends"] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": False,
    }

if DEBUG:
    import sys

    is_testing = "test" in sys.argv or any("pytest" in arg for arg in sys.argv)
    if not is_testing:
        INSTALLED_APPS.append("debug_toolbar")  # noqa: F405
        INSTALLED_APPS.append("silk")  # noqa: F405
        MIDDLEWARE.insert(0, "silk.middleware.SilkyMiddleware")  # noqa: F405
        dt_middleware = "debug_toolbar.middleware.DebugToolbarMiddleware"
        MIDDLEWARE.insert(1, dt_middleware)  # noqa: F405
