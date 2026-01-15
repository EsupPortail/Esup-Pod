import os

# FORCE ENABLE AUTH PROVIDERS FOR TESTS
# We set these environment variables BEFORE importing dev/base settings
# so that src.config.settings.authentication reads them as True.
os.environ["USE_CAS"] = "True"
os.environ["USE_LDAP"] = "True"
os.environ["USE_SHIB"] = "True"
os.environ["USE_OIDC"] = "True"

from config.django.dev.docker import *  # noqa: F401, F403
from config.env import env

# TESTS SETTINGS
DEBUG = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# External/Async Services Disabled
CELERY_TASK_ALWAYS_EAGER = True

# TEST DATABASES
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pod_db",  # Standard dev DB (unused in tests)
        "USER": env("MYSQL_USER", default="pod"),
        "PASSWORD": env("MYSQL_PASSWORD", default="pod"),
        "HOST": env("MYSQL_HOST", default="db"),
        "PORT": env("MYSQL_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
        "TEST": {
            "NAME": "test_pod_db",  # Pre-created in init_test_db.sql
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_general_ci",
        },
    }
}
