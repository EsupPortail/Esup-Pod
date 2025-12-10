import os
from config.env import BASE_DIR, env

env.read_env(os.path.join(BASE_DIR, '.env'))

POD_VERSION = env("VERSION")
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
    'rest_framework_simplejwt',
    "corsheaders",
    "drf_spectacular",
    'django_cas_ng',
    'src.apps.utils',
    'src.apps.authentication',
    'src.apps.info',
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
    'django_cas_ng.middleware.CASMiddleware',
    'src.apps.authentication.IPRestrictionMiddleware.IPRestrictionMiddleware',
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
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LANGUAGE_CODE = 'en-en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
SITE_ID = 1

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

##
# Applications settings (and settings locale if any)
#
# Add settings
for application in INSTALLED_APPS:
    if application.startswith("src"):
        path = application.replace(".", os.path.sep) + "/base.py"
        if os.path.exists(path):
            _temp = __import__(application, globals(), locals(), ["settings"])
            for variable in dir(_temp.settings):
                if variable == variable.upper():
                    locals()[variable] = getattr(_temp.settings, variable)
# add local settings
for application in INSTALLED_APPS:
    if application.startswith("src"):
        path = application.replace(".", os.path.sep) + "/settings_local.py"
        if os.path.exists(path):
            _temp = __import__(application, globals(), locals(), ["settings_local"])
            for variable in dir(_temp.settings_local):
                if variable == variable.upper():
                    locals()[variable] = getattr(_temp.settings_local, variable)

from config.settings.authentication import *
from config.settings.swagger import *

CAS_SERVER_URL = "https://cas.univ-lille.fr"
CAS_VERSION = '3'
CAS_FORCE_CHANGE_USERNAME_CASE = 'lower'
CAS_APPLY_ATTRIBUTES_TO_USER = True

LDAP_SERVER = {
    "url": "ldap://ldap.univ.fr", 
    "port": 389, 
    "use_ssl": False
}

AUTH_LDAP_BIND_DN = "cn=pod,ou=app,dc=univ,dc=fr" 
AUTH_LDAP_BIND_PASSWORD =  os.getenv("AUTH_LDAP_BIND_PASSWORD", "")

AUTH_LDAP_USER_SEARCH = ("ou=people,dc=univ,dc=fr", "(uid=%(uid)s)")

USER_LDAP_MAPPING_ATTRIBUTES = {
    "uid": "uid",
    "mail": "mail",
    "last_name": "sn",
    "first_name": "givenname",
    "primaryAffiliation": "eduPersonPrimaryAffiliation",
    "affiliations": "eduPersonAffiliation",
    "groups": "memberOf",
    "establishment": "establishment",
}

AFFILIATION_STAFF = ("faculty", "employee", "staff")
CREATE_GROUP_FROM_AFFILIATION = False
CREATE_GROUP_FROM_GROUPS = True
POPULATE_USER = "CAS"

SHIBBOLETH_ATTRIBUTE_MAP = {
    "REMOTE_USER": (True, "username"),
    "Shibboleth-givenName": (True, "first_name"),
    "Shibboleth-sn": (False, "last_name"),
    "Shibboleth-mail": (False, "email"),
    "Shibboleth-primary-affiliation": (False, "affiliation"),
    "Shibboleth-unscoped-affiliation": (False, "affiliations"),
}

SHIBBOLETH_STAFF_ALLOWED_DOMAINS = []

OIDC_CLAIM_GIVEN_NAME = "given_name"
OIDC_CLAIM_FAMILY_NAME = "family_name"
OIDC_CLAIM_PREFERRED_USERNAME = "preferred_username"

OIDC_DEFAULT_AFFILIATION = "member"
OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = []
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "mon-client-id")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "mon-secret")

OIDC_OP_TOKEN_ENDPOINT = os.environ.get(
    "OIDC_OP_TOKEN_ENDPOINT", 
    "https://auth.example.com/oidc/token"
)

OIDC_OP_USER_ENDPOINT = os.environ.get(
    "OIDC_OP_USER_ENDPOINT", 
    "https://auth.example.com/oidc/userinfo"
)

ALLOWED_SUPERUSER_IPS = ["127.0.0.1", "10.0.0.0/8"]

USE_CAS = True  

USE_LDAP = False 

USE_LOCAL_AUTH = True
