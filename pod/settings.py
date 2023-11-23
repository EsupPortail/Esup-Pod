"""
Django global settings for pod_project.

Django version: 3.2.
"""
import os
import importlib.util

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# will be update in pod/main/settings.py

##
# Version of the project
#
VERSION = "3.5.0"

##
# Installed applications list
#
INSTALLED_APPS = [
    # put in first https://github.com/deschler/django-
    # modeltranslation/issues/408 AND http://django-modeltranslation.
    # readthedocs.io/en/latest/installation.html#installed-apps
    "modeltranslation",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",
    # Exterior Applications
    "ckeditor",
    "sorl.thumbnail",
    "tagging",
    "cas",
    "captcha",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "django_select2",
    "shibboleth",
    "chunked_upload",
    "mozilla_django_oidc",
    "honeypot",
    "lti_provider",
    "pwa",
    "webpush",
    # Pod Applications
    "pod.main",
    "django.contrib.admin",  # put it here for template override
    "pod.authentication",
    "pod.video",
    "pod.podfile",
    "pod.playlist",
    "pod.completion",
    "pod.chapter",
    "pod.enrichment",
    "pod.video_search",
    "pod.live",
    "pod.recorder",
    "pod.lti",
    "pod.bbb",
    "pod.meeting",
    "pod.cut",
    "pod.xapi",
    "pod.video_encode_transcript",
    "pod.import_video",
    "pod.progressive_web_app",
    "pod.dressing",
    "pod.custom",
]

##
# Activated middleware components
#
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Pages statiques
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
]


AUTHENTICATION_BACKENDS = ("pod.main.auth_backend.SiteBackend",)

##
# Full Python import path to root URL file
#
ROOT_URLCONF = "pod.urls"

##
# Full Python path of WSGI app object Django's built-in-servers
# (e.g. runserver) will use
#
WSGI_APPLICATION = "pod.wsgi.application"

##
# Settings for all template engines to be used
#
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "DIRS": [],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Local contexts
                "pod.main.context_processors.context_settings",
                "pod.main.context_processors.context_footer",
                "pod.video.context_processors.context_video_data",
                "pod.video.context_processors.context_video_settings",
                "pod.authentication.context_processors.context_authentication_settings",
                "pod.recorder.context_processors.context_recorder_settings",
                "pod.playlist.context_processors.context_settings",
                "pod.import_video.context_processors.context_settings",
            ],
        },
    },
]

##
# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.{0}".format(validator)}
    for validator in [
        "UserAttributeSimilarityValidator",
        "MinimumLengthValidator",
        "CommonPasswordValidator",
        "NumericPasswordValidator",
    ]
]

##
# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = (os.path.join(BASE_DIR, "pod", "locale"),)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

##
# Time zone support is enabled (True) or not (False)
#
USE_TZ = True

##
# WEBservices with rest API
#
# curl -X GET http://127.0.0.1:8000/api/example/ -H 'Authorization: Token
# 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b'
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAdminUser",),
    "DEFAULT_PAGINATION_CLASS": ("rest_framework.pagination.PageNumberPagination"),
    "PAGE_SIZE": 12,
}


##
# Logging configuration https://docs.djangoproject.com/en/3.2/topics/logging/
#
LOG_DIRECTORY = os.path.join(BASE_DIR, "pod", "log")
if not os.path.exists(LOG_DIRECTORY):
    os.mkdir(LOG_DIRECTORY)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "general": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s - %(filename)s:%(lineno)s] %(message)s "
            "(EXCEPTION: %(exc_info)s)",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "request": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s - %(filename)s:%(lineno)s] %(message)s "
            "(STATUS: %(status_code)s; REQUEST: %(request)s; EXCEPTION: %(exc_info)s)",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "db": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s - %(filename)s:%(lineno)s] %(message)s "
            "(DURATION: %(duration)s; SQL: %(sql)s; PARAMS: %(params)s; EXCEPTION: %(exc_info)s)",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
    },
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "general",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
        "django": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "django.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "general",
        },
        "security": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "security.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "general",
        },
        "db": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "db.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "db",
        },
        "request": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "request.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "request",
        },
        "celery": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "celery.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "general",
        },
        "delayed_tasks": {
            "level": "INFO",
            # 'filters': ['require_debug_false'],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "delayed_tasks.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "general",
        },
        "apps": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "apps.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "general",
        },
        "api": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIRECTORY, "api.log"),
            "maxBytes": 16 * 1024 * 1024,  # 16 MB
            "backupCount": 5,
            "formatter": "general",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["django"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["request", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["db", "mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "celery": {
            "handlers": ["celery"],
            "level": "ERROR",
        },
        "celery.task": {
            "handlers": ["delayed_tasks"],
            "level": "INFO",
        },
        "apps": {
            "handlers": ["apps"],
            "level": "WARNING",
        },
        "common": {
            "handlers": ["apps"],
            "level": "WARNING",
        },
        "api": {
            "handlers": ["api"],
            "level": "ERROR",
        },
        "py.warnings": {
            "handlers": ["console"],
            "propagate": False,
        },
        "": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "pod",
    },
    "select2": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}
SESSION_ENGINE = "redis_sessions.session"
SESSION_REDIS = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 4,
    "prefix": "session",
    "socket_timeout": 1,
    "retry_on_timeout": False,
}

# Tell select2 which cache configuration to use:
SELECT2_CACHE_BACKEND = "select2"

MODELTRANSLATION_FALLBACK_LANGUAGES = ("fr", "en")

# MIGRATION_MODULES = {
#     'flatpages': 'pod.db_migrations'
# }


##
# Applications settings (and settings locale if any)
#
# Add settings
for application in INSTALLED_APPS:
    if application.startswith("pod"):
        path = application.replace(".", os.path.sep) + "/settings.py"
        if os.path.exists(path):
            _temp = __import__(application, globals(), locals(), ["settings"])
            for variable in dir(_temp.settings):
                if variable == variable.upper():
                    locals()[variable] = getattr(_temp.settings, variable)
# add local settings
for application in INSTALLED_APPS:
    if application.startswith("pod"):
        path = application.replace(".", os.path.sep) + "/settings_local.py"
        if os.path.exists(path):
            _temp = __import__(application, globals(), locals(), ["settings_local"])
            for variable in dir(_temp.settings_local):
                if variable == variable.upper():
                    locals()[variable] = getattr(_temp.settings_local, variable)

STATICFILES_DIRS = [os.path.join(BASE_DIR, "node_modules")]


def update_settings(local_settings):
    ##
    # AUTH
    #
    if local_settings.get("USE_CAS", False):
        local_settings["AUTHENTICATION_BACKENDS"] += ("cas.backends.CASBackend",)
        local_settings["CAS_RESPONSE_CALLBACKS"] = (
            "pod.authentication.populatedCASbackend.populateUser",
            # function call to add some information to user login by CAS
        )
        local_settings["MIDDLEWARE"].append("cas.middleware.CASMiddleware")

    if local_settings.get("USE_SHIB", False):
        local_settings["AUTHENTICATION_BACKENDS"] += (
            "pod.authentication.backends.ShibbBackend",
        )
        local_settings["MIDDLEWARE"].append(
            "pod.authentication.shibmiddleware.ShibbMiddleware"
        )
    if local_settings.get("USE_OIDC", False):
        local_settings["AUTHENTICATION_BACKENDS"] += (
            "pod.authentication.backends.OIDCBackend",
        )
        local_settings["LOGIN_REDIRECT_URL"] = "/"
    ##
    # Authentication backend: add lti backend if use
    #
    if local_settings.get("LTI_ENABLED", False):
        local_settings["AUTHENTICATION_BACKENDS"] += ("lti_provider.auth.LTIBackend",)

    ##
    # Opencast studio
    if local_settings.get("USE_OPENCAST_STUDIO", False):
        # add dir to opencast studio static files i.e: pod/custom/static/opencast/
        local_settings["TEMPLATES"][0]["DIRS"].append(
            os.path.join(BASE_DIR, "custom", "static", "opencast")
        )

    local_settings["AUTHENTICATION_BACKENDS"] = list(
        dict.fromkeys(local_settings["AUTHENTICATION_BACKENDS"])
    )

    return local_settings


the_update_settings = update_settings(locals())
for variable in the_update_settings:
    locals()[variable] = the_update_settings[variable]

if locals()["DEBUG"] is True and importlib.util.find_spec("debug_toolbar") is not None:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ] + MIDDLEWARE
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": "pod.settings.show_toolbar"}

    def show_toolbar(request):
        return True
