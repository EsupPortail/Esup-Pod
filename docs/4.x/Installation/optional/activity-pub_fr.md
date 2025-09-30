---
layout: default
version: 4.x
lang: fr
---

# Mise en place du protocole ActivityPub

> ⚠️ Fonctionnalité non disponible à l'heure actuelle sur Pod v4.

## Configuration

Une paire de clés RSA est nécessaire pour ActivityPub.
Elles peuvent être générées ainsi :

```python
from Crypto.PublicKey import RSA

activitypub_key = RSA.generate(2048)

# Generate the private key
# Add the content of this command in 'pod/custom/settings_local.py'
# in a variable named ACTIVITYPUB_PRIVATE_KEY
with open("pod/activitypub/ap.key", "w") as fd:
    fd.write(activitypub_key.export_key().decode())
# Generate the public key
# Add the content of this command in 'pod/custom/settings_local.py'
# in a variable named ACTIVITYPUB_PUBLIC_KEY
with open("pod/activitypub/ap.pub", "w") as fd:
    fd.write(activitypub_key.publickey().export_key().decode())
```

Ajouter la configuration Celery/Redis dans le fichier `settings_local.py` :

```bash
pod@pod:/usr/local/django_projects/podv3$ nano pod/custom/settings_local.py
# Configuration ActivityPub
USE_ACTIVITYPUB = True
ACTIVITYPUB_CELERY_BROKER_URL = "redis://127.0.0.1:6379/7"  # on utilise la db 7 comme espace file d’attente sur redis

with open("pod/activitypub/ap.key") as fd:
    ACTIVITYPUB_PRIVATE_KEY = fd.read()

with open("pod/activitypub/ap.pub") as fd:
    ACTIVITYPUB_PUBLIC_KEY = fd.read()
```

## Activer Celery

Mettre le contenu de
[https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd](https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd)
dans `/etc/init.d/celeryd-activitypub`

```bash
pod@pod:~$ sudo nano /etc/init.d/celeryd-activitypub
pod@pod:~$ sudo chmod u+x /etc/init.d/celeryd-activitypub
```

Puis créer le fichier default associé :

```bash
pod@pod:~$ sudo nano /etc/default/celeryd-activitypub
CELERYD_NODES="worker-activitypub"                                     # Nom du/des worker(s). Ajoutez autant de workers que de tâches à exécuter en parallèle.
CELERY_BIN="/home/pod/.virtualenvs/django_pod/bin/celery"               # répertoire source de celery
CELERY_APP="pod.activitypub.tasks"                                     # application où se situe celery
CELERYD_CHDIR="/usr/local/django_projects/podv3"                         # répertoire du projet Pod (où se trouve manage.py)
CELERYD_OPTS="--time-limit=86400 --concurrency=1 --max-tasks-per-child=1  --prefetch-multiplier=1" # options supplémentaires pour le(s) worker(s)
CELERYD_LOG_FILE="/var/log/celery/%N.log"                              # fichier de log
CELERYD_PID_FILE="/var/run/celery/%N.pid"                              # fichier pid
CELERYD_USER="pod"                                                     # utilisateur système exécutant celery
CELERYD_GROUP="pod"                                                    # groupe système exécutant celery
CELERY_CREATE_DIRS=1                                                   # si celery a le droit de créer des dossiers
CELERYD_LOG_LEVEL="INFO"                                               # niveau de log
```

### Vérifier que tout est OK

```bash
(django_pod) pod@pod:/usr/local/django_projects/podv3$ celery --app pod.activitypub.tasks worker --loglevel INFO --queues activitypub --concurrency 1 --hostname activitypub
```

## Démarrer Celeryd

```bash
pod@pod:~$ sudo /etc/init.d/celeryd-activitypub start
```

Lancer Celeryd automatiquement au redémarrage du serveur :

```bash
pod@pod:~$ sudo systemd-sysv-install enable celeryd-activitypub
```

Pour vérifier si Celery fonctionne correctement :

```bash
(django_pod) pod@pod:/usr/local/django_projects/podv3$ celery --broker=redis://127.0.0.1:6379/7 inspect active
```
