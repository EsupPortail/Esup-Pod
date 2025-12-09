from .base import * 

DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False 
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")