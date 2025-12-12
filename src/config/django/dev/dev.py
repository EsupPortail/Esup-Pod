import logging
from ..base import *

DEBUG = True
SHOW_SQL_QUERIES = True
CORS_ALLOW_ALL_ORIGINS = True
ALLOWED_HOSTS = ["*"]

class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[94m",    # blue
        "INFO": "\033[92m",     # green
        "WARNING": "\033[93m",  # yellow
        "ERROR": "\033[91m",    # red
        "CRITICAL": "\033[95m", # magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": ColoredFormatter,
            "format": "{levelname} {asctime} [{module}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "colored",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO", 
            "propagate": False,
        },
        "django.utils.autoreload": {
            "handlers": ["console"],
            "level": "WARNING", 
            "propagate": False,
        },
        "pod": {
            "handlers": ["console"],
            "level": "DEBUG",  
            "propagate": False,
        },
        "rest_framework_simplejwt": {
            "handlers": ["console"],
            "level": "WARNING", 
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