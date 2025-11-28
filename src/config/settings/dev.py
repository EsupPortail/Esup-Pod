from .base import *
import os  # Bonne pratique : expliciter l'import si on l'utilise ici, même si base l'importe déjà

# Surcharge spécifique pour le développement
DEBUG = True

# Tu pourras ajouter ici des outils de debug (Django Debug Toolbar, etc.)
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
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        # Logger par défaut pour Django
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        # Votre logger spécifique au projet "pod"
        "pod": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}