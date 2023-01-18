"""Django local settings for pod_project.Django version : 1.11.10."""

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
# N'oubliez ps de renseigner la SECERT_KEY django (https://djecrety.ir/)
SECRET_KEY = '<MY_SECRET_KEY>'

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
#ALLOWED_HOSTS = ['localhost', '192.168.1.8']
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']
ALLOWED_HOSTS = ['*']

##
# A tuple that lists people who get code error notifications
#   when DEBUG=False and a view raises an exception.
#
# https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-ADMINS
#
ADMINS = (
    ('Name', 'XXX@univ-XXX.fr'),
)
# configuration exemple pour utiliser une base de données MySql,
# voir ci-apprès l'installation de lib tierce nécessaire
# il est possible d'utiliser d'autres moteur de bases de données (PostGreSql...)
# https://docs.djangoproject.com/fr/1.11/ref/databases/
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydatabase',
        'USER': 'mydatabaseuser',
        'PASSWORD': 'mypassword',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET storage_engine=INNODB, sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
         },
    }
}
'''
##
# Internationalization and localization.
#
# https://docs.djangoproject.com/en/1.11/topics/i18n/
# https://github.com/django/django/blob/master/django/conf/global_settings.py
LANGUAGES = (
    ('fr', 'Français'),
    ('en', 'English')
)

#Hide Users in navbar
HIDE_USER_TAB = True
# Hide Types tab in navbar
HIDE_TYPES_TAB = True
# Hide Tags
HIDE_TAGS = True
# Hide disciplines in navbar
HIDE_DISCIPLINES = True

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
EMAIL_HOST = 'smtp.univ-XXX.fr'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'noreply@univ-XXX.fr'

# https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-SERVER_EMAIL
SERVER_EMAIL = 'noreply@univ-XXX.fr'

##
# THIRD PARTY APPS OPTIONNAL
#
USE_PODFILE = True

##
# TEMPLATE Settings
#
TEMPLATE_VISIBLE_SETTINGS = {

    'TITLE_SITE': 'XXX.Pod',
    'TITLE_ETB': 'Université de XXX',
    'LOGO_SITE': 'img/logoPod.svg',
    'LOGO_COMPACT_SITE': 'img/logoPod.svg',
    'LOGO_ETB': 'img/logo_etb.svg',
    'LOGO_PLAYER': 'img/logoPod.svg',
    'FOOTER_TEXT': (
        '42, rue Paul Duez',
        '59000 Lille - France',
        ('<a href="https://goo.gl/maps/AZnyBK4hHaM2"'
         ' target="_blank">Google maps</a>')
    ),
    'LINK_PLAYER': 'http://www.univ-XXX.fr',
    # 'CSS_OVERRIDE': 'custom/mycss.css',
    'PRE_HEADER_TEMPLATE': ''
}
# Choose a theme for your pod website
# 'default' is the simpliest, bootstrap $enable_rounded is true
# 'green' is with a dark green for primary color, $enable_rounded is false
# 'dark' is black and red, without grey background, $enable_rounded is false
# USE_THEME = 'green'

# Custom Bootstrap CSS file. Example : custom/bootstrap-default.min.css
# BOOTSTRAP_CUSTOM = ''

ES_VERSION = 7

ES_URL = ['http://elasticsearch:9200/']