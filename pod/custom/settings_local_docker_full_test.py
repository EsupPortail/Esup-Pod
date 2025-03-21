DEBUG = True

TEST_REMOTE_ENCODE = True
TEST_SETTINGS = True

ALLOWED_HOSTS = ["*"]

ADMINS = (
    ('Nicolas', 'nicolas@univ.fr'),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        'NAME': '/usr/src/app/pod/db_remote.sqlite3',
        'TEST': {
            'NAME': '/usr/src/app/pod/db_remote.sqlite3',
        },
        "OPTIONS": {
            "timeout": 40.0,  # in seconds
            # see also https://docs.python.org/3.10/library/sqlite3.html#sqlite3.connect
        },
    }
}

USE_CUT = True
USE_PODFILE = True
USE_NOTIFICATIONS = False
EMAIL_ON_ENCODING_COMPLETION = False
SECRET_KEY = 'A_CHANGER'

# ElasticSearch version
ES_VERSION = 8
ES_URL = ['http://elasticsearch.localhost:9200/']
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis.localhost:6379/3',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'pod'
    },
    'select2': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis.localhost:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    },
}
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS = {
    'host': 'redis.localhost',
    'port': 6379,
    'db': 4,
    'prefix': 'session',
    'socket_timeout': 1,
    'retry_on_timeout': False,
}

# Only in containerized environments
MIGRATION_MODULES = {'flatpages': 'pod.db_migrations'}

# If DOCKER_ENV = full: activate encoding, transcription and remote xapi
USE_REMOTE_ENCODING_TRANSCODING = True
ENCODING_TRANSCODING_CELERY_BROKER_URL = 'redis://redis.localhost:6379/7'
POD_API_URL = "http://pod.localhost:8000/rest"
POD_API_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

USE_TRANSCRIPTION = True
TRANSCRIPTION_TYPE = "WHISPER"
TRANSCRIPTION_MODEL_PARAM = {
    'WHISPER': {
        'fr': {
            'model': "small",
            'download_root': "/usr/src/app/transcription/whisper/",
        },
        'en': {
            'model': "small",
            'download_root': "/usr/src/app/transcription/whisper/",
        }
    }
}

USE_XAPI_VIDEO = False
XAPI_CELERY_BROKER_URL = "redis://redis.localhost:6379/6"

# for maximum console logging\n
LOGGING = {}
