"""
Django local settings for pod_project.
Django version : 1.11.10.
"""

import os
from .lang_settings import ALL_LANG_CHOICES, PREF_LANG_CHOICES

##
# flatpages
##
SITE_ID = 1

# Lang choices
LANG_CHOICES = (
    (' ', PREF_LANG_CHOICES),
    ('----------', ALL_LANG_CHOICES)
)
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
# Session settings
#
# https://docs.djangoproject.com/en/1.11/ref/settings/#session-cookie-age
# https://docs.djangoproject.com/en/1.11/ref/settings/#session-expire-at-browser-close
#
SESSION_COOKIE_AGE = 14400
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

##
# A tuple that lists people who get code error notifications
#   when DEBUG=False and a view raises an exception.
#
# https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-ADMINS
#
ADMINS = (
    ('Name', 'adminmail@univ.fr'),
)
##
# A tuple that lists people who get other notifications
#   email from contact_us / end of encoding / report video
#
# https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-MANAGERS
MANAGERS = ADMINS
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
# https://github.com/django/django/blob/master/django/conf/global_settings.py
LANGUAGE_CODE = 'fr'
LANGUAGES = (
    ('fr', 'Français'),
    ('en', 'English'),
    ('nl', 'Dutch (Netherlands)')
)

##
# A string representing the time zone for this installation.
#
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE = 'UTC'

##
# The directory to temporarily store data while uploading files.
#
#   If None, the standard temporary directory for the operating system
#   will be used.
#
# https://docs.djangoproject.com/en/1.11/ref/settings/#file-upload-temp-dir
#
FILE_UPLOAD_TEMP_DIR = os.path.join(os.path.sep, 'var', 'tmp')
# https://github.com/ouhouhsami/django-progressbarupload
FILE_UPLOAD_HANDLERS = (
    "progressbarupload.uploadhandler.ProgressBarUploadHandler",
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)
PROGRESSBARUPLOAD_INCLUDE_JQUERY = False

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
# CKeditor settings
#
# CKEDITOR_BASEPATH = os.path.join(STATIC_URL, 'ckeditor', "/")
CKEDITOR_UPLOAD_PATH = os.path.join(MEDIA_ROOT, 'uploads')
CKEDITOR_CONFIGS = {
    'complete': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%'
    },
    'default': {
        'height': 300,
        'width': '100%',
        'toolbar': 'custom',
        'language': 'fr',
        'toolbar_custom': [
            {'name': 'basicstyles', 'items': [
                'Bold', 'Italic', 'Underline', 'Strike', 'Subscript',
                'Superscript', '-', 'RemoveFormat'
            ]
            },
            {'name': 'paragraph', 'items': [
                'NumberedList', 'BulletedList',
                '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv',
                '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight',
                'JustifyBlock', '-', 'BidiLtr', 'BidiRtl'
            ]},
            {'name': 'links', 'items': ['Link', 'Unlink', 'Anchor']},
            {'name': 'tools', 'items': ['Maximize']}
        ],
    }
}

##
# Main menu settings:
#
# Do not show inactive users in “Owners” main menu list.
MENUBAR_HIDE_INACTIVE_OWNERS = True
# Show only staff users in “Owners” main menu list.
MENUBAR_SHOW_STAFF_OWNERS_ONLY = False

##
# Video tiers apps settings
#
FORCE_LOWERCASE_TAGS = True
MAX_TAG_LENGTH = 50

##
# AUTH CAS
#
LOGIN_URL = '/authentication_login/'


##
# eMail settings
#
# https://docs.djangoproject.com/en/1.11/ref/settings/#email-host
# https://docs.djangoproject.com/en/1.11/ref/settings/#email-port
# https://docs.djangoproject.com/en/1.11/ref/settings/#default-from-email
#
#   username: EMAIL_HOST_USER
#   password: EMAIL_HOST_PASSWORD
#
EMAIL_HOST = 'smtp.univ.fr'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'noreply@univ.fr'

# https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-SERVER_EMAIL
SERVER_EMAIL = 'noreply@univ.fr'

##
# Captcha config
#
CAPTCHA_CHALLENGE_FUNCT = 'captcha.helpers.math_challenge'
# ('captcha.helpers.noise_arcs','captcha.helpers.noise_dots',)
CAPTCHA_NOISE_FUNCTIONS = ('captcha.helpers.noise_null',)

##
# THIRD PARTY APPS OPTIONNAL
#
USE_PODFILE = False
THIRD_PARTY_APPS = []

##
# https://docs.djangoproject.com/fr/1.11/ref/clickjacking/
#
X_FRAME_OPTIONS = 'EXEMPT'  # SAMEORIGIN, DENY OR EXEMPT

###
# Enable LTI Provider
# https://github.com/ccnmtl/django-lti-provider
#   if True
# LTI_ENABLED=False default

LTI_TOOL_CONFIGURATION = {
    'title': 'LTI Pod',
    'description': 'Pod description',
    'launch_url': 'lti/',
    'embed_url': '',
    'embed_icon_url': '',
    'embed_tool_id': '',
    'landing_url': '/',
    'course_aware': False,
    'course_navigation': True,
    'new_tab': True,
    'frame_width': 640,
    'frame_height': 360,
    'assignments': {
        'addvideo': '/assignment/addvideo/',
        'getvideo': '/assignment/getvideo/'

    }
}

PYLTI_CONFIG = {
    'consumers': {
        'azerty': {
            'secret': 'azerty'
        }
    }
}
LTI_PROPERTY_LIST_EX = [
    'custom_canvas_user_login_id',
    'ext_user_username',
    'context_title',
    'lis_course_offering_sourcedid',
    'custom_canvas_api_domain',
    'custom_video'
]
LTI_PROPERTY_USER_USERNAME = 'ext_user_username'
