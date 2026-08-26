"""
Esup-Pod - Base Django configuration.

Core settings shared across all environments (dev, test, prod).
Defines installed apps, middleware, template engines, DRF configuration,
and static/media file paths.

REFACTOR NOTE:
Configuration is now modular. Feature flags and app-specific settings
should be placed in `src/config/settings/{app_name}.py`.
"""

import logging


from config.env import BASE_DIR, env

logger = logging.getLogger(__name__)

# Read .env file (Secrets only) - already handled in config.env
# env.read_env(os.path.join(BASE_DIR, ".env"))

# Core settings
POD_VERSION = env("VERSION", default="5.0.0-DEV")
POD_PROJECT_NAME = f"POD V{POD_VERSION.split('.')[0]}"
SECRET_KEY = env("SECRET_KEY")
SITE_URL = env("SITE_URL", default="http://localhost:8000")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_cas_ng",
    "django_filters",
    "src.apps.utils",
    "src.apps.authentication",
    "src.apps.info",
    "src.apps.core",
    "src.apps.video",
    "src.apps.notes",
    "src.apps.encoding",
    "tagulous",
    "src.apps.collection",
    "src.apps.completion",
    "src.apps.dressing",
    "src.apps.migration",
    "src.apps.import_video",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_cas_ng.middleware.CASMiddleware",
    "src.apps.authentication.IPRestrictionMiddleware.IPRestrictionMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# In src/config/django/base.py

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": env.int("API_PAGE_SIZE", default=20),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Pod REST API",
    "DESCRIPTION": "Video management API (Local Authentication)",
    "VERSION": POD_VERSION,
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = "en-en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
SITE_ID = 1

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# ==============================================================================
# CELERY CONFIGURATION
# ==============================================================================
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://redis:6379/0")

# ==============================================================================
# CACHE & SESSION CONFIGURATION (Role 1 & 2 of POD V4)
# ==============================================================================
REDIS_CACHE_URL = env("REDIS_CACHE_URL", default=None)
REDIS_SESSION_URL = env("REDIS_SESSION_URL", default=None)
REDIS_PASSWORD = env("REDIS_PASSWORD", default=None)

if REDIS_CACHE_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_CACHE_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "PASSWORD": REDIS_PASSWORD,
                "IGNORE_EXCEPTIONS": True,
            },
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }

CACHE_TIMEOUT = env.int("CACHE_TIMEOUT", default=600)

if REDIS_SESSION_URL:
    SESSION_ENGINE = "redis_sessions.session"
    SESSION_REDIS = {
        "url": REDIS_SESSION_URL,
        "password": REDIS_PASSWORD,
        "prefix": "session",
        "socket_timeout": 1,
    }

INTERNAL_IPS = env.list("INTERNAL_IPS", default=["localhost", "127.0.0.1"])

# ==============================================================================
# MODULAR SETTINGS LOADING
# ==============================================================================
# 1. Load Defaults: src/config/defaults/{app}.py
# 2. Load Overrides: src/config/settings/{app}.py (local customization)

APPS_WITH_CUSTOM_SETTINGS = [
    "authentication",
    "video",
    "swagger",
    "core",
    "encoding",
    "collection",
    "completion",
    "import_video",
]


def _load_settings_from_module(module_path):
    """Load uppercase settings from a module into globals."""
    try:
        mod = __import__(module_path, fromlist=["*"])
        for setting_name in dir(mod):
            if setting_name.isupper():
                globals()[setting_name] = getattr(mod, setting_name)
    except ImportError:
        logger.debug("Optional settings module not found, skipping: %s", module_path)


for app_config_name in APPS_WITH_CUSTOM_SETTINGS:
    _load_settings_from_module(f"src.config.defaults.{app_config_name}")
    _load_settings_from_module(f"src.config.settings.{app_config_name}")

if not globals().get("CORS_ALLOWED_ORIGINS") and not globals().get(
    "CORS_ALLOW_ALL_ORIGINS"
):
    import warnings

    warnings.warn(
        "CORS_ALLOWED_ORIGINS is empty. Cross-origin requests will fail.", stacklevel=2
    )

# ==============================================================================
# TAGULOUS CONFIGURATION
# ==============================================================================
SERIALIZATION_MODULES = {
    "xml": "tagulous.serializers.xml_serializer",
    "json": "tagulous.serializers.json",
    "python": "tagulous.serializers.python",
    "yaml": "tagulous.serializers.pyyaml",
}
