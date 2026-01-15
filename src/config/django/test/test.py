import os
from ..base import *  # noqa: F401, F403
from config.django.test.init_env import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("TEST_DB_NAME", ":memory:"),
    }
}

ALLOWED_HOSTS = ["*"]
