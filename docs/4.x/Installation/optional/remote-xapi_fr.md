---
layout: default
version: 4.x
lang: fr
---

# Mise en place de l'xAPI sur le serveur d'encodage

> ⚠️ Documentation à tester sur un Pod v4.

> Nous appellerons dans la suite de cette documentation, serveur `frontal` le serveur où la partie web serveur est installée et serveur `encodage` le serveur où est déportée la tâche xAPI

## Schéma de principe de fonctionnement

![Schéma Pod xAPI](remote-xapi_screens/xapi1.png)

## Activation sur le serveur frontal

Ajouter la configuration Celery/Redis dans le fichier `settings_local.py` :

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

# Configuration Celery sur le frontal
USE_XAPI = True
XAPI_ANONYMIZE_ACTOR = False
XAPI_LRS_LOGIN = "XXX"
XAPI_LRS_PWD = "XXX"
XAPI_LRS_URL = "http://monserveurLRS/xAPI/statements/"
USE_XAPI_VIDEO = True
XAPI_CELERY_BROKER_URL = "redis://redis:6379/6"  # on utilise la db6 comme espace file d’attente sur redis
```

## Installation sur le serveur d’encodage

Il faut installer Pod **sans réinitialiser la base** et sans nginx/uwsgi/Elasticsearch. Vous pouvez suivre la doc d’installation de la plateforme Pod.

### Ajouter la configuration correspondante dans le fichier settings

Il faut maintenant indiquer au serveur d’encodage :

* qu’on souhaite utiliser CELERY
* l’adresse du serveur frontal comme BROKER pour CELERY

```bash
(django_pod4) pod@pod-encodage:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

USE_XAPI = True
XAPI_ANONYMIZE_ACTOR = False
XAPI_LRS_LOGIN = "XXX"
XAPI_LRS_PWD = "XXX"
XAPI_LRS_URL = "http://monserveurLRS/xAPI/statements/"
USE_XAPI_VIDEO = True
XAPI_CELERY_BROKER_URL = "redis://redis:6379/6"  # on utilise la db6 comme espace file d’attente sur redis
```

#### Activer Celery sur le serveur d’encodage

Mettre le contenu de
[https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd](https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd)
dans `/etc/init.d/celeryd`

```bash
(django_pod4) pod@pod-enc:~/django_projects/podv4$ sudo vim /etc/init.d/celeryd-xapi
(django_pod4) pod@pod-enc:~/django_projects/podv4$ sudo chmod u+x /etc/init.d/celeryd-xapi
```

Puis créer le fichier default associé :

```bash
(django_pod4) pod@pod-enc:/usr/local/django_projects/podv4$ sudo vim /etc/default/celeryd-xapi

CELERYD_NODES="worker-xapi"                                              # Nom du/des worker(s). Ajoutez autant de workers que de tâches à exécuter en parallèle.
DJANGO_SETTINGS_MODULE="pod.settings"                                  # settings de votre Pod
CELERY_BIN="/home/pod/.virtualenvs/django_pod/bin/celery"              # répertoire source de celery
CELERY_APP="pod.xapi.xapi_tasks"                                       # application où se situe celery
CELERY_ROUTES = {"pod.xapi.xapi_tasks.*": {"queue": "xapi"}}
CELERYD_CHDIR="/usr/local/django_projects/podv4"                       # répertoire du projet Pod (où se trouve manage.py)
CELERYD_OPTS="--time-limit=86400 --concurrency=1 --max-tasks-per-child=1 --prefetch-multiplier=1"  # options supplémentaires pour le(s) worker(s)
CELERYD_LOG_FILE="/var/log/celery/%N.log"                              # fichier log
CELERYD_PID_FILE="/var/run/celery/%N.pid"                              # fichier pid
CELERYD_USER="pod"                                                     # utilisateur système utilisant celery
CELERYD_GROUP="pod"                                                    # groupe système utilisant celery
CELERY_CREATE_DIRS=1                                                   # si celery dispose du droit de création de dossiers
CELERYD_LOG_LEVEL="INFO"                                               # niveau d’information inscrit dans les logs
```

### Démarrer Celeryd

```bash
(django_pod4) pod@pod-enc:~/django_projects/podv4$ sudo /etc/init.d/celeryd-xapi start
```

Pour vérifier si Celery fonctionne bien :

```bash
celery -A pod.xapi.xapi_tasks -l INFO -Q xapi --concurrency 1 -n xapi
```
