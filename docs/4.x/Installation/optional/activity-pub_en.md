---
layout: default
version: 4.x
lang: en
---

# Setting up the ActivityPub protocol

> ⚠️ Feature currently not available on Pod v4.

## Configuration

An RSA key pair is required for ActivityPub.
It can be generated as follows:

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

Add the Celery/Redis configuration in the `settings_local.py` file:

```bash
pod@pod:/usr/local/django_projects/podv4$ nano pod/custom/settings_local.py
# ActivityPub configuration
USE_ACTIVITYPUB = True
ACTIVITYPUB_CELERY_BROKER_URL = "redis://127.0.0.1:6379/7"  # using db 7 as the queue space in redis

with open("pod/activitypub/ap.key") as fd:
    ACTIVITYPUB_PRIVATE_KEY = fd.read()

with open("pod/activitypub/ap.pub") as fd:
    ACTIVITYPUB_PUBLIC_KEY = fd.read()
```

## Enable Celery

Put the content of
[https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd](https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd)
into `/etc/init.d/celeryd-activitypub`

```bash
pod@pod:~$ sudo nano /etc/init.d/celeryd-activitypub
pod@pod:~$ sudo chmod u+x /etc/init.d/celeryd-activitypub
```

Then create the associated default file:

```bash
pod@pod:~$ sudo nano /etc/default/celeryd-activitypub
CELERYD_NODES="worker-activitypub"                                     # Name of the worker(s). Add as many workers as tasks to run in parallel.
CELERY_BIN="/home/pod/.virtualenvs/django_pod/bin/celery"              # celery source directory
CELERY_APP="pod.activitypub.tasks"                                     # application where celery is located
CELERYD_CHDIR="/usr/local/django_projects/podv4"                       # Pod project directory (where manage.py is located)
CELERYD_OPTS="--time-limit=86400 --concurrency=1 --max-tasks-per-child=1 --prefetch-multiplier=1" # extra options for the worker(s)
CELERYD_LOG_FILE="/var/log/celery/%N.log"                              # log file
CELERYD_PID_FILE="/var/run/celery/%N.pid"                              # pid file
CELERYD_USER="pod"                                                     # system user running celery
CELERYD_GROUP="pod"                                                    # system group running celery
CELERY_CREATE_DIRS=1                                                   # whether celery can create directories
CELERYD_LOG_LEVEL="INFO"                                               # log level
```

### Check that everything is OK

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ celery --app pod.activitypub.tasks worker --loglevel INFO --queues activitypub --concurrency 1 --hostname activitypub
```

## Start Celeryd

```bash
pod@pod:~$ sudo /etc/init.d/celeryd-activitypub start
```

Launch Celeryd automatically on server reboot:

```bash
pod@pod:~$ sudo systemd-sysv-install enable celeryd-activitypub
```

To check if Celery is working correctly:

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ celery --broker=redis://127.0.0.1:6379/7 inspect active
```
