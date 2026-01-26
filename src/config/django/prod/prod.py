from config.env import env

from ..base import *  # noqa: F401, F403

DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
