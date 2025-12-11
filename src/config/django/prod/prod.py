from ..base import * 
from config.env import env

DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False 
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])