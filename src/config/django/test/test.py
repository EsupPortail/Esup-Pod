from ..base import *

USE_LOCAL_AUTH = True
USE_CAS = False
USE_LDAP = False
USE_SHIB = False
USE_OIDC = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ALLOWED_HOSTS = ["*"]
