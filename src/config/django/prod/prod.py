from ..base import *  # noqa: F401, F403
from config.env import env

DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])