"""
Django local settings for pod_project.
Django version : 1.11.10.
"""
from pod import settings


import os
##
# flatpages
##
SITE_ID = 1

##
# The secret key for your particular Django installation.
#
# This is used to provide cryptographic signing,
# and should be set to a unique, unpredictable value.
#
# Django will not start if this is not set.
# https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key
#
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'A_CHANGER'

##
# Base folder
#
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

##
# DEBUG mode activation
#
# https://docs.djangoproject.com/en/1.11/ref/settings/#debug
#
# SECURITY WARNING: MUST be set to False when deploying into production.
DEBUG = True

##
# A list of strings representing the host/domain names
# that this Django site is allowed to serve.
#
# https://docs.djangoproject.com/en/1.11/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost']

##
# A dictionary containing the settings for all databases
# to be used with Django.
#
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

##
# Internationalization and localization.
#
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = 'fr'
LANGUAGES = (
    ('fr', 'Français'),
    ('en', 'English'),
    ('nl-NL', 'Dutch (Netherlands)')
)

##
# A string representing the time zone for this installation.
#
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE = 'UTC'

##
# Static files (assets, CSS, JavaScript, fonts...)
#
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

##
# Dynamic files (user managed content: videos, subtitles, documents, etc...)
#
# https://docs.djangoproject.com/en/1.11/ref/settings/#media-url
# https://docs.djangoproject.com/en/1.11/ref/settings/#media-root
#
# WARNING: this folder must have previously been created.
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

##
# Template settings
#
TEMPLATE_THEME = 'DEFAULT'
TITLE_SITE = 'Pod'

##
# CKeditor settings
#
CKEDITOR_BASEPATH = os.path.join(
    getattr(settings, 'STATIC_URL', '/static/'), 'ckeditor', 'ckeditor') + "/"

##
# Main menu settings:
#
# Do not show inactive users in “Owners” main menu list.
MENUBAR_HIDE_INACTIVE_OWNERS = False
# Show only staff users in “Owners” main menu list.
MENUBAR_SHOW_STAFF_OWNERS_ONLY = False
