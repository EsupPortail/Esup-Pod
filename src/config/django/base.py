"""
Base Django configuration.

Core settings shared across all environments (dev, test, prod).
Defines installed apps, middleware, template engines, DRF configuration,
and static/media file paths.

REFACTOR NOTE:
Configuration is now modular. Feature flags and app-specific settings
should be placed in `src/config/settings/{app_name}.py`.
"""

import os


from config.env import BASE_DIR, env

# Read .env file (Secrets only)
env.read_env(os.path.join(BASE_DIR, ".env"))

# Core settings
POD_VERSION = env("VERSION", default="5.0.0-DEV")
SECRET_KEY = env("SECRET_KEY")

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
    "corsheaders",
    "drf_spectacular",
    "django_cas_ng",
    "src.apps.utils",
    "src.apps.authentication",
    "src.apps.info",
    "src.apps.core",
    "src.apps.video",
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

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
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
# MODULAR SETTINGS LOADING
# ==============================================================================
# 1. Load Defaults: src/config/defaults/{app}.py
# 2. Load Overrides: src/config/settings/{app}.py (local customization)

APPS_WITH_CUSTOM_SETTINGS = [
    "authentication",
    "video",
    "swagger",
    "core",
]


def _load_settings_from_module(module_path):
    """Load uppercase settings from a module into globals."""
    try:
        mod = __import__(module_path, fromlist=["*"])
        for setting_name in dir(mod):
            if setting_name.isupper():
                globals()[setting_name] = getattr(mod, setting_name)
    except ImportError:
        pass  # Module not found, skip


for app_config_name in APPS_WITH_CUSTOM_SETTINGS:
    _load_settings_from_module(f"src.config.defaults.{app_config_name}")
    _load_settings_from_module(f"src.config.settings.{app_config_name}")
