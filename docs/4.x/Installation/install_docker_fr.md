---
layout: default
version: 4.x
lang: fr
---

# Installation Docker

Télécharger et installer Docker <https://www.docker.com>

## Récupération des sources

```sh
(django_pod4) pod@pod:~/django_projects$ git clone https://github.com/EsupPortail/Esup-Pod.git podv4
Clonage dans "podv4"...
remote: Counting objects: 4578, done.
remote: Compressing objects: 100% (378/378), done.
remote: Total 4578 (delta 460), reused 564 (delta 348), pack-reused 3847
Réception d’objets: 100% (4578/4578), 4.40 MiB | 3.88 MiB/s, fait.
Résolution des deltas: 100% (3076/3076), fait.
```

puis

```sh
(django_pod4) pod@pod:~/django_projects$ cd podv4/
```

L’ensemble des fichiers dockerfile se trouvent dans le répertoire _/dockerfile-dev-with-volumes_

Pour faciliter la contruction de la stack plusieurs commandes préfixées de docker-xxx ont été ajoutées dans le fichier _Makefile_ est disponible à la racine du projet et utilise le fichier _env.dev_ pour les paramètres de construction.

### Configuration

1. Renommer le fichier _.env.dev-exemple_ en _.env.dev_ situé à la racine du projet et le renseigner.
    Vous devez changer les valeurs d’identifiant, mot de passe et courriel.

    ```py
    DJANGO_SUPERUSER_USERNAME=admin
    DJANGO_SUPERUSER_PASSWORD=admin
    DJANGO_SUPERUSER_EMAIL=celine.didier@univ-lorraine.fr
    ```

    Pour la variable DOCKER_ENV, vous pouvez choisir entre _light_ (1 docker pour Pod avec que l’encodage d’activé) ou _full_ (4 docker pour Pod : pod-back, encodage, transcription et xAPI)

    ```py
    DOCKER_ENV=light
    ```

2. Créer un fichier _pod/custom/settings_local.py_

Renseignez le fichier _pod/custom/settings_local.py_ comme ceci :

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

#### Construction des conteneurs

- Se positionner à la racine du projet
- Sous windows, devez remplacer _make_ par _make.bat_.

##### Build et démarrage de la stack

```sh
## Force la recompilation des conteneurs (obligatoire au premier lancement ou après un docker-reset)
$ make docker-build
```

Suppression des répertoires suivants :

```sh
./pod/log
./pod/static
./pod/node_modules
```

##### Démarrage de la stack

```sh
## Lancement sans recompilation des conteneurs, ni suppressions répertoires ./pod/log, ./pod/static, ./pod/node_modules
$ make docker-start
```

Attention, il a été constaté que sur un mac, le premier lancement peut prendre plus de 5 minutes. ;)

Vous devriez obtenir ce message une fois esup-pod lancé

```sh
pod-dev-with-volumes | Superuser created successfully.
```

L’application esup-pod est dès lors disponible via cette URL : pod.localhost:8000

##### Arrêt de la stack

`CTRL+C` dans la fenetre depuis laquelle l’application esup-pod a été lancée

OU depuis une autre fenêtre via

```sh
podv4$ make docker-stop
```

##### Reset de la stack

Cette commande supprime l’ensemble des données crées depuis le/les conteneur(s) via les volumes montés

```sh
podv4$ make docker-reset
```

Suppression des répertoires suivants :

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

## Détail des images

### Conteneur ElasticSearch

<http://elasticsearch.localhost:9200>

#### elasticsearch:8.16.1

#### OS/ARCH

```conf
linux/amd64
linux/arm64/v8
```

### Conteneur Redis

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

### Conteneur Python / FFMPEG (esup-pod)

#### OS/ARCH esup-pod

```conf
linux/386
linux/amd64
linux/arm/v7
linux/arm64/v8
```
