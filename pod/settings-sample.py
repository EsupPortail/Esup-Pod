"""
Django global settings for pod_project.

Django version : 1.11.10.
"""
import os

##
# Local and applications settings import
#
from .settings_local import (
    SECRET_KEY, 
    BASE_DIR,
    DEBUG,
    DATABASES,
    LANGUAGE_CODE,
    LANGUAGES,
    TIME_ZONE,
    STATIC_URL,
    STATIC_ROOT,
    MEDIA_URL,
    MEDIA_ROOT,
    TEMPLATE_THEME,
    TITLE_SITE,
)


##
# Version of the project
#
VERSION = '2.0.0'

##
# Installed applications list
#
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Exterior Applications
    'bootstrap4',
    # Pod Applications
    'pod.main',
]

##
# Activated middleware components
#
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

##
# Full Python import path to root URL file
#
ROOT_URLCONF = 'pod.urls'

##
# Full Python path of WSGI app object Django's built-in-servers
# (e.g. runserver) will use
#
WSGI_APPLICATION = 'pod.wsgi.application'

##
# Settings for all template engines to be used
#
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'theme', TEMPLATE_THEME, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Local contexts
                'pod.main.context_processors.context_settings'
            ],
        },
    },
]

##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = (
    'TITLE_SITE',
)

##
# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': "django.contrib.auth.password_validation.{0}".format(validator)}
    for validator in [
        'UserAttributeSimilarityValidator',
        'MinimumLengthValidator',
        'CommonPasswordValidator',
        'NumericPasswordValidator',
    ]
]

##
# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/
USE_I18N = True
USE_L10N = True

##
# Time zone support is enabled (True) or not (False)
#
USE_TZ = True
