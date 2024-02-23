import os
import binascii

DEBUG = True

TEST_REMOTE_ENCODE = True
TEST_SETTINGS = True

ALLOWED_HOSTS = ["*"]

ADMINS = (
    ('Nicolas', 'nicolas@univ.fr'),
)

USE_PODFILE = True
USE_NOTIFICATIONS = False
EMAIL_ON_ENCODING_COMPLETION = False
SECRET_KEY = 'A_CHANGER'

# on précise ici qu'on utilise ES version 7\n
ES_VERSION = 7
ES_URL = ['http://elasticsearch:9200/']
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/3',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'pod'
    },
    'select2': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
}
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS = {
    'host': 'redis',
    'port': 6379,
    'db': 4,
    'prefix': 'session',
    'socket_timeout': 1,
    'retry_on_timeout': False,
}

# Uniquement lors d’environnement conteneurisé
MIGRATION_MODULES = {'flatpages': 'pod.db_migrations'}

# Si DOCKER_ENV = full il faut activer l'encodage, la transcription et l'xapi distante
USE_REMOTE_ENCODING_TRANSCODING = True
ENCODING_TRANSCODING_CELERY_BROKER_URL = 'redis://redis:6379/7'
POD_API_URL = "http://pod-back:8080/rest"
POD_API_TOKEN = binascii.hexlify(os.urandom(20)).decode()

USE_XAPI_VIDEO = False
XAPI_CELERY_BROKER_URL = "redis://redis:6379/6"

# pour avoir le maximum de log sur la console\n
LOGGING = {}
