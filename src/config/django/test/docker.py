from config.django.dev.docker import *  # noqa: F401, F403
from config.env import env

# Enable Authentication Providers for Docker/CI Tests
USE_LOCAL_AUTH = True
USE_CAS = True
USE_LDAP = True
USE_SHIB = True
USE_OIDC = True

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
