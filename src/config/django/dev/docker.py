from .dev import *  # noqa: F401, F403
from config.env import env

# Enable Authentication Providers for Docker/CI Tests
USE_LOCAL_AUTH = True
USE_CAS = True
USE_LDAP = True
USE_SHIB = True
USE_OIDC = True

# Uncomment for debugging
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]


# DEFAULT CONFIG (Docker environment): MariaDB
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("MYSQL_DATABASE", default="pod_db"),
        "USER": env("MYSQL_USER", default="pod"),
        "PASSWORD": env("MYSQL_PASSWORD", default="pod"),
        "HOST": env("MYSQL_HOST", default="localhost"),
        "PORT": env("MYSQL_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
