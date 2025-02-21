---
layout: default
version: 4.x
lang: en
---

# Docker Installation

Download and install Docker <https://www.docker.com>

## Source retrieval

```sh
(django_pod4) pod@pod:~/django_projects$ git clone https://github.com/EsupPortail/Esup-Pod.git podv4
Cloning in “podv4”...
remote: Counting objects: 4578, done.
remote: Compressing objects: 100% (378/378), done.
remote: Total 4578 (delta 460), reused 564 (delta 348), pack-reused 3847
Receiving objects: 100% (4578/4578), 4.40 MiB | 3.88 MiB/s, done.
Delta resolution: 100% (3076/3076), done.
```

then

```sh
(django_pod4) pod@pod:~/django_projects$ cd podv4/
```

All dockerfile files are located in the _/dockerfile-dev-with-volumes_ directory.

To facilitate stack construction, several prefixed docker-xxx commands have been added to the _Makefile_ file, which is available at the root of the project and uses the _env.dev_ file for construction parameters.

### Settings

1. Rename the _.env.dev-example_ file to _.env.dev_ located at the root of the project and fill it in.
    You must change the values for login, password and e-mail.

    ```py
    DJANGO_SUPERUSER_USERNAME=admin
    DJANGO_SUPERUSER_PASSWORD=admin
    DJANGO_SUPERUSER_EMAIL=celine.didier@univ-lorraine.fr
    ```
   
    For the DOCKER_ENV variable, you can choose between _light_ (1 Pod docker with only encoding enabled) or _full_ (4 Pod dockers: pod-back, encoding, transcription and xAPI).

    ```py
    DOCKER_ENV=light
    ```

2. Create a _pod/custom/settings_local.py_ file

Fill in the _pod/custom/settings_local.py_ file as follows:

```py
USE_PODFILE = True
EMAIL_ON_ENCODING_COMPLETION = False
SECRET_KEY = "A_CHANGER"
DEBUG = True
## on précise ici qu’on utilise ES version 8
ES_VERSION = 8
ES_URL = ["http://elasticsearch.localhost:9200/"]


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis.localhost:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "pod"
    },
    "select2": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis.localhost:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}
SESSION_ENGINE = "redis_sessions.session"
SESSION_REDIS = {
    "host": "redis.localhost",
    "port": 6379,
    "db": 4,
    "prefix": "session",
    "socket_timeout": 1,
    "retry_on_timeout": False,
}

## Uniquement lors d’environnement conteneurisé
MIGRATION_MODULES = {"flatpages": "pod.db_migrations"}

## Si DOCKER_ENV = full il faut activer l’encodage et la transcription distante
## USE_REMOTE_ENCODING_TRANSCODING = True
## ENCODING_TRANSCODING_CELERY_BROKER_URL = "redis://redis.localhost:6379/7"

## pour avoir le maximum de log sur la console
LOGGING = {}

## PUSH NOTIFICATIONS
## Les clés VAPID peuvent être générées avec https://web-push-codelab.glitch.me/
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "",
    "VAPID_PRIVATE_KEY": "",
    "VAPID_ADMIN_EMAIL": "contact@example.org"
}
```

#### Container construction

- Position at project root
- Under Windows, replace _make_ with _make.bat_.

##### Build and start stack

```sh
## Force container recompilation (mandatory at first launch or after docker-reset)
$ make docker-build
```

Delete the following directories:

```sh
./pod/log
./pod/static
./pod/node_modules
```

##### Start stack

```sh
## Launch without recompiling containers or deleting directories ./pod/log, ./pod/static, ./pod/node_modules
$ make docker-start
```

Please note that on a Mac, the first launch can take more than 5 minutes ;)

You should get this message once esup-pod has been launched

```sh
pod-dev-with-volumes | Superuser created successfully.
```

The esup-pod application is now available via this URL: pod.localhost:8000

##### Stack stop

CTRL+C` in the window from which the esup-pod application was launched

OR from another window via

```sh
podv4$ make docker-stop
```

##### Stack reset

This command deletes all data created from the container(s) via mounted volumes.

```sh
podv4$ make docker-reset
```

Deletes the following directories:

```sh
./pod/log
./pod/media
./pod/static
./pod/node_modules
./pod/db_migrations
./pod/db.sqlite3
./pod/yarn.lock
```

---

---

## Image details

### ElasticSearch container

<http://elasticsearch.localhost:9200>

#### elasticsearch:8.16.1

#### OS/ARCH

```conf
linux/amd64
linux/arm64/v8
```

### Redis container

#### OS/ARCH Redis

```conf
linux/386
linux/amd64
linux/arm/v6
linux/arm/v7
linux/arm64/v8
linux/ppc64le
linux/s390x
```

### Python / FFMPEG container (esup-pod)

#### OS/ARCH esup-pod

```conf
linux/386
linux/amd64
linux/arm/v7
linux/arm64/v8
```

