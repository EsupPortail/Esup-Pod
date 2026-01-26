from config.django.test.init_env import *  # noqa: F401, F403
from config.django.dev.docker import *  # noqa: F401, F403
from config.env import env

DEBUG = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CELERY_TASK_ALWAYS_EAGER = True

# TEST DATABASES
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "pod_db",
        "USER": env("MYSQL_USER", default="pod"),
        "PASSWORD": env("MYSQL_PASSWORD", default="pod"),
        "HOST": env("MYSQL_HOST", default="db"),
        "PORT": env("MYSQL_PORT", default="3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
        "TEST": {
            "NAME": "test_pod_db",
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_general_ci",
        },
    }
}
