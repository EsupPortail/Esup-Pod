---
layout: default
version: 4.x
lang: en
---

# Setting up xAPI on the encoding server

> ⚠️ Documentation to be tested on a Pod v4.

> In this documentation, we will call `frontal` server the one where the web server part is installed, and `encoding` server the one where the xAPI task is offloaded.

## Functional principle diagram

![Pod xAPI Diagram](remote-xapi_screens/xapi1.png)

## Activation on the frontal server

Add the Celery/Redis configuration in the `settings_local.py` file:

```bash
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

# Celery configuration on the frontal
USE_XAPI = True
XAPI_ANONYMIZE_ACTOR = False
XAPI_LRS_LOGIN = "XXX"
XAPI_LRS_PWD = "XXX"
XAPI_LRS_URL = "http://myLRSserver/xAPI/statements/"
USE_XAPI_VIDEO = True
XAPI_CELERY_BROKER_URL = "redis://redis:6379/6"  # we use db6 as the queue space on redis
```

## Installation on the encoding server

Pod must be installed **without resetting the database** and without nginx/uwsgi/Elasticsearch. You can follow the Pod platform installation documentation.

### Add the corresponding configuration in the settings file

You must now indicate to the encoding server:

* that we want to use CELERY
* the address of the frontal server as the BROKER for CELERY

```bash
(django_pod4) pod@pod-encoding:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py

USE_XAPI = True
XAPI_ANONYMIZE_ACTOR = False
XAPI_LRS_LOGIN = "XXX"
XAPI_LRS_PWD = "XXX"
XAPI_LRS_URL = "http://myLRSserver/xAPI/statements/"
USE_XAPI_VIDEO = True
XAPI_CELERY_BROKER_URL = "redis://redis:6379/6"  # we use db6 as the queue space on redis
```

#### Enable Celery on the encoding server

Put the content of
[https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd](https://raw.githubusercontent.com/celery/celery/main/extra/generic-init.d/celeryd)
into `/etc/init.d/celeryd`

```bash
(django_pod4) pod@pod-enc:~/django_projects/podv4$ sudo vim /etc/init.d/celeryd-xapi
(django_pod4) pod@pod-enc:~/django_projects/podv4$ sudo chmod u+x /etc/init.d/celeryd-xapi
```

Then create the associated default file:

```bash
(django_pod4) pod@pod-enc:/usr/local/django_projects/podv4$ sudo vim /etc/default/celeryd-xapi

CELERYD_NODES="worker-xapi"                                            # Name of the worker(s). Add as many workers as tasks to run in parallel.
DJANGO_SETTINGS_MODULE="pod.settings"                                  # your Pod settings
CELERY_BIN="/home/pod/.virtualenvs/django_pod/bin/celery"              # celery source directory
CELERY_APP="pod.xapi.xapi_tasks"                                       # application where celery is located
CELERY_ROUTES = {"pod.xapi.xapi_tasks.*": {"queue": "xapi"}}
CELERYD_CHDIR="/usr/local/django_projects/podv4"                       # Pod project directory (where manage.py is located)
CELERYD_OPTS="--time-limit=86400 --concurrency=1 --max-tasks-per-child=1 --prefetch-multiplier=1"  # additional options for the worker(s)
CELERYD_LOG_FILE="/var/log/celery/%N.log"                              # log file
CELERYD_PID_FILE="/var/run/celery/%N.pid"                              # pid file
CELERYD_USER="pod"                                                     # system user running celery
CELERYD_GROUP="pod"                                                    # system group running celery
CELERY_CREATE_DIRS=1                                                   # if celery has rights to create directories
CELERYD_LOG_LEVEL="INFO"                                               # log information level
```

### Start Celeryd

```bash
(django_pod4) pod@pod-enc:~/django_projects/podv4$ sudo /etc/init.d/celeryd-xapi start
```

To check if Celery is working properly:

```bash
celery -A pod.xapi.xapi_tasks -l INFO -Q xapi --concurrency 1 -n xapi
```
