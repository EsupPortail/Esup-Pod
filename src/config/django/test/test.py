import os   
from ..base import *  # noqa: F401, F403

USE_LOCAL_AUTH = True
USE_CAS = True
USE_LDAP = True
USE_SHIB = True
USE_OIDC = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("TEST_DB_NAME", ":memory:"),
    }
}

ALLOWED_HOSTS = ["*"]
