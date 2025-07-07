---
layout: default
version: 4.x
lang: en
---

# Configuration and use of REDIS

## Introducing REDIS

Redis (REmote DIctionary Server) is an extremely fast NoSQL **key-value** database, mainly used as a **cache**, **queue** and **message engine**.
It operates in memory (RAM), which enables it to offer much better performance than traditional databases for certain tasks.

In Pod, REDIS is used as a :
 - cache manager for **Web servers**,
 - encoding/transcription/xAPI task queue manager for **encoding servers**, in addition to **Celery**. Only in the case of remote encoding on other servers (notion of Celery Broker)_.

At present, it is an essential building block for the operation of Pod.

## REDIS configuration for Pod

### List of useful databases

| Base identifier | Comments                        |
|------------------------|-------------------------------------|
| 2 | Base for the select2 plugin (useful for selection lists) |
| 3 | Base for the backend |
| 4 | Base for sessions |
| 5 | Base for encoding and transcoding |
| 6 | Base for xAPI |
{: .table .table-striped}

### Effective configuration

Configuration is carried out in your custom/settings_local.py file:

```sh
# To use traditional remote encoding
CELERY_TO_ENCODE = True
# REDIS broker URL
CELERY_BROKER_URL = "redis://127.0.0.1:6379/5"
# Allows only one task to be processed at a time
CELERY_TASK_ACKS_LATE = True
# Cache management
CACHES = {
  'default': {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/3',
    'OPTIONS': {
      'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
  },
  'select2': {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/2',
    'OPTIONS': {
      'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
  },
}
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS = {
  'host': '127.0.0.1',
  'port': 6379,
  'db': 4,
  'prefix': 'session',
  'socket_timeout': 1,
  'retry_on_timeout': False
}
# Tell select2 which cache configuration to use
SELECT2_CACHE_BACKEND = "select2"
```

> ⚠️ Depending on your architecture, remember to replace _127.0.0.1_ with the **IP address of the REDIS server**, see [installation documentation](../install_standalone_en#redis).
