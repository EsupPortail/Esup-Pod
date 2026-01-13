from ..base import *  # noqa: F401, F403
import logging
import sqlparse
import re

DEBUG = True
SHOW_SQL_QUERIES = False
CORS_ALLOW_ALL_ORIGINS = True
ALLOWED_HOSTS = ["*"]


class ColoredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    LEVEL_COLORS = {
        logging.DEBUG: blue,
        logging.INFO: green,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red,
    }

    def format(self, record):
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

        if record.name == "django.db.backends":
            record.name = "[DB]"
        elif record.name == "django.server":
            record.name = "[HTTP]"
        elif record.name.startswith("django"):
            record.name = "[DJANGO]"
        if record.name == "[DB]" and sqlparse and hasattr(record, "sql"):
            pass

        formatted_msg = super().format(record)

        if record.name == "[DB]" and sqlparse and "SELECT" in formatted_msg:
            formatted_msg = sqlparse.format(
                formatted_msg, reindent=True, keyword_case="upper"
            )
            formatted_msg = f"{self.grey}{formatted_msg}{self.reset}"

        return formatted_msg


# --- FILTRES ---
class SkipIgnorableRequests(logging.Filter):
    """Filtre pour ignorer les bruits de fond du dev server."""

    def filter(self, record):
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
            "format": "%(levelname)s %(asctime)s %(name)-10s %(message)s",
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
        "pod": {
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
