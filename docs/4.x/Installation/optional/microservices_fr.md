---
layout: default
version: 4.x
lang: fr
---

# Mise en place des microservices d’encodage, de transcodage et de xAPI

> ⚠️ Documentation à tester sur un Pod v4.

Depuis la version 3.4.0, il est possible de déporter l’encodage, la transcription et l’xAPI en micro-service. Ces micro-services sont autonomes et ne nécessitent pas de lien avec la base de données ou le moteur de recherche comme précédemment.

Cela se fait selon le schéma suivant :

![Schéma de fonctionnement](microservices_screens/microservices1.png)

Vous disposez de **dockerfiles** pour chaque micro-service dans le code source de Pod :

- Encodage : [https://github.com/EsupPortail/Esup-Pod/blob/main/dockerfile-dev-with-volumes/pod-encode/Dockerfile](https://github.com/EsupPortail/Esup-Pod/blob/main/dockerfile-dev-with-volumes/pod-encode/Dockerfile)
- Transcription : [https://github.com/EsupPortail/Esup-Pod/blob/main/dockerfile-dev-with-volumes/pod-transcript/Dockerfile](https://github.com/EsupPortail/Esup-Pod/blob/main/dockerfile-dev-with-volumes/pod-transcript/Dockerfile)
- xAPI : [https://github.com/EsupPortail/Esup-Pod/blob/main/dockerfile-dev-with-volumes/pod-xapi/Dockerfile](https://github.com/EsupPortail/Esup-Pod/blob/main/dockerfile-dev-with-volumes/pod-xapi/Dockerfile)

Il faut que chaque service ait accès au même espace de fichiers Pod (espace partagé) et un accès à Redis qui jouera le rôle de file d’attente pour les tâches d’encodage, de transcription ou d’envoi xAPI.

Chaque micro-service est lancé via une commande Celery.

## Microservice Encodage

> Nous appellerons dans cette documentation le **serveur Pod backend** le serveur où la partie web est installée, et **serveur Pod encodage** le serveur où est déporté l’encodage.

### Pré-requis

- Il faut que votre répertoire `podv4` du serveur backend soit partagé entre vos serveurs (montage NFS par exemple).

### Configuration sur le serveur Pod backend

Dans le fichier `settings_local.py` :

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

# Configuration Celery sur le frontal
USE_REMOTE_ENCODING_TRANSCODING = True
ENCODING_TRANSCODING_CELERY_BROKER_URL = "redis://redis:6379/5"
```

### Installation sur le serveur d’encodage

Installation des dépendances système :

```bash
(django_pod4) pod@pod-encodage:/usr/local/django_projects/podv4$ apt-get update && apt-get install -y ffmpeg \
    ffmpegthumbnailer \
    imagemagick
```

Installation des bibliothèques Python (dans un environnement virtuel) :

```bash
(django_pod4) pod@pod-encodage:/usr/local/django_projects/podv4$ pip3 install --no-cache-dir -r requirements-encode.txt
```

Configuration requise dans le fichier `settings_local.py` :

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

# Configuration sur le serveur d’encodage
# Adresse de l’API REST à appeler en fin d’encodage ou transcription distante :
POD_API_URL = "https://pod.univ.fr/rest/"
# Token d’authentification utilisé pour l’appel après encodage distant ou transcription
POD_API_TOKEN = "xxxx"
```

Il suffit ensuite de lancer Celery via :

```bash
(django_pod4) pod@pod-encodage:/usr/local/django_projects/podv4$ celery -A pod.video_encode_transcript.encoding_tasks worker -l INFO -Q encoding --concurrency 1 -n encode
```

## Microservice Transcodage

> Nous appellerons dans cette documentation le **serveur Pod backend** le serveur où la partie web est installée, et **serveur Pod transcodage** le serveur où est effectué le transcodage.

### Pré-requis

Il faut que votre répertoire `podv4` du serveur backend soit partagé entre vos serveurs (montage NFS par exemple).

### Configuration sur le serveur Pod backend

Dans le fichier `settings_local.py` :

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

# Configuration Celery sur le frontal
USE_REMOTE_ENCODING_TRANSCODING = True
ENCODING_TRANSCODING_CELERY_BROKER_URL = "redis://redis:6379/5"
```

### Installation sur le serveur de transcodage

Installation des dépendances système :

```bash
(django_pod4) pod@pod-transcodage:/usr/local/django_projects/podv4$ apt-get update && apt-get install -y sox libsox-fmt-mp3
```

Installation des bibliothèques Python :

```bash
(django_pod4) pod@pod-transcodage:/usr/local/django_projects/podv4$ pip3 install --no-cache-dir -r requirements-transcripts.txt \
    && pip3 install --no-cache-dir -r requirements-encode.txt
```

Configuration requise dans `settings_local.py` :

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

# Adresse de l’API REST à appeler en fin d’encodage ou transcription distante :
POD_API_URL = "https://pod.univ.fr/rest/"
# Token d’authentification pour l’appel après traitement distant :
POD_API_TOKEN = "xxxx"
```

Puis lancer Celery :

```bash
(django_pod4) pod@pod-transcodage:/usr/local/django_projects/podv4$ celery -A pod.video_encode_transcript.transcripting_tasks worker -l INFO -Q transcripting --concurrency 1 -n transcript
```

## Microservice xAPI

> Nous appellerons dans cette documentation le **serveur Pod backend** le serveur où la partie web est installée, et **serveur Pod xAPI** le serveur où est effectué le traitement xAPI.

### Pré-requis

Il faut que votre répertoire `podv4` du serveur backend soit partagé entre vos serveurs (montage NFS par exemple).

### Configuration sur le serveur Pod backend

Dans `settings_local.py` :

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

USE_XAPI = True
XAPI_ANONYMIZE_ACTOR = False
XAPI_LRS_LOGIN = "XXXX"
XAPI_LRS_PWD = "XXXXX"
XAPI_LRS_URL = "http://xapi.univ.fr/xAPI/statements/"
USE_XAPI_VIDEO = True
XAPI_CELERY_BROKER_URL = "redis://redis:6379/6"
```

### Installation sur le serveur de traitement xAPI

Installation des dépendances Python dans un environnement virtuel (identiques à celles de l’encodage) :

```bash
(django_pod4) pod@pod-transcodage:/usr/local/django_projects/podv4$ pip3 install --no-cache-dir -r requirements-encode.txt
```

Il suffit ensuite de lancer Celery :

```bash
(django_pod4) pod@pod-transcodage:/usr/local/django_projects/podv4$ celery -A pod.xapi.xapi_tasks worker -l INFO -Q xapi --concurrency 1 -n xapi
```

## Monitoring

Pour monitorer la liste des encodages en cours ou en attente, vous pouvez utiliser l’outil `celery` en ligne de commande.

Placez-vous donc dans l’environnement virtuel django et lancez les commandes suivantes, en remplacant <ID> par le thread Redis voulu (5 pour les encodages, 6 pour xAPI par exemple).

Pour les tâches en cours :

```bash
(django_pod4) pod@pod-transcodage:/$ celery --broker=redis://redis:6379/<ID> inspect active
```

Pour les tâches en attente :

```bash
(django_pod4) pod@pod-transcodage:/$ celery --broker=redis://redis:6379/<ID> inspect reserved
```
