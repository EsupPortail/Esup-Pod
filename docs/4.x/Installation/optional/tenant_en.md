---
layout: default
version: 4.x
lang: en
---

# Setting up multiple tenants

> ⚠️ Documentation to be tested on a Pod v4.

Setting up multiple tenants on your Pod application will allow you to host 2 Pod instances while having only one Pod installation. You could therefore have `pod1.univ.fr` and `pod2.univ.fr`. Each instance will have its own users, its own videos, and its own settings.

## Pre-configuration in Pod

Before actually setting up multi-tenants, you must make sure to properly configure your sites in your administration space.

A "site" in Django is equivalent to a tenant. Each site object is linked to a domain name, a name, and a unique identifier.

In the site administration (`Administration > Sites > Site`), you must therefore create a second site (or more, depending on your needs) which will have its own domain name.

## Deployment with Nginx

To set up multi-tenants on Pod, you need to correctly configure your Nginx server. Several tenants will therefore mean several uwsgi processes, one per tenant.

Thus, you just need to take the Pod installation documentation in the "Production deployment" section and repeat the procedure as many times as you have sites.

When setting up the second site, you will need to rename the necessary Nginx configuration files with different names than those of the first site. For example:

```bash
pod@pod:~/django_projects/podv4$ cp pod_nginx.conf pod/custom/pod_nginx2.conf
pod@pod:~/django_projects/podv4$ vim pod/custom/pod_nginx2.conf
pod@pod:~/django_projects/podv4$ sudo ln -s /usr/local/django_projects/podv4/pod/custom/pod_nginx2.conf /etc/nginx/sites-enabled/pod_nginx2.conf
pod@pod:~/django_projects/podv4$ sudo /etc/init.d/nginx restart
pod@pod:~/django_projects/podv4$ cp pod_uwsgi.ini pod_uwsgi2.ini
pod@pod:~/django_projects/podv4$ cp pod_uwsgi2.ini pod/custom/.
pod@pod:~/django_projects/podv4$ sudo uwsgi --ini pod/custom/pod_uwsgi2.ini --enable-threads --daemonize /usr/local/django_projects/podv4/pod/log/uwsgi-pod2.log --uid pod2 --gid www-data --pidfile /tmp/pod2.pid
````

### Special case: the `.ini` file

Regarding the `pod_uwsgi2.ini` file, you will need to modify the socket path:

```ini
socket = /home/pod/django_projects/podv4/pod4v2.sock
```

You must also use a custom settings file. To do this, add this line at the end of the `.ini` file:

```ini
env = DJANGO_SETTINGS_MODULE=pod.sites2_settings
```

### The settings file

Once deployment is complete, a few adjustments need to be made in the newly created settings file.

The file must contain at least these two lines:

```python
from .settings import *
SITE_ID = 2
ES_INDEX = 'pod'
```

In this file, it is possible to override any Pod setting for this specific site.

Example usage:

```bash
python manage.py <command> --settings=pod.sites2_settings
```

This is particularly necessary when updating the ElasticSearch index.

## Creating "Admin site"

Any user with **superuser** status will be able to log into all deployed Pod instances.
However, if you want to have site-specific administrators, proceed as follows:

* In each site's administration, create a group "Site Admin" (or another name of your choice) and assign it the desired permissions.
* Add users to this group.

The people in the "Site Admin" group will therefore only have permissions on the site associated with that group.

## Setup command

Diagram:

```bash
NGINX-VHOST
 -> uwsgi socket
     -> uwsgi ini file
         -> per-tenant config file (tenant_settings.py)
```

Each tenant must have its own site identifier (`SITE_ID=2`).

Example file:

```python
from .settings import *
SITE_ID = 2
ES_INDEX = 'podtenant'
ALLOWED_HOSTS = ['video.tenant.fr']
DEFAULT_FROM_EMAIL = 'no-reply@tenant.fr'
SERVER_EMAIL = 'no-reply@tenant.fr'
HELP_MAIL = 'no-reply@tenant.fr'
CONTACT_US_EMAIL = ['contact@tenant.fr']
```

Additional settings:

```python
TEMPLATE_VISIBLE_SETTINGS = {
    'TITLE_SITE': 'tenant.Video',
    'TITLE_ETB': 'Tenant title',
    'LOGO_SITE': 'img/logoPod.svg',
    'LOGO_COMPACT_SITE': 'img/logoPod.svg',
    'LOGO_ETB': 'tenant/custom/images/tenant-logo-1.png',
    'LOGO_PLAYER': 'img/logoPod.svg',
    'FOOTER_TEXT': (''),
    'LINK_PLAYER': 'https://www.tenant.fr/',
    'CSS_OVERRIDE': 'tenant/custom/override.css',
}

CELERY_TO_ENCODE = True
CELERY_BROKER_URL = "amqp://pod:p0drabbit@localhost/rabbitpod-tenant"
```

Each command must be launched with the tenant's settings file:

```bash
python manage.py runserver tenant:8080 --settings=pod.tenant_settings
python manage.py index_videos --all --settings=pod.tenant_settings
```

### Cron tasks

```bash
0 3 * * * cd /usr/local/django_projects/podv4 && /home/pod/.virtualenvs/django_pod/bin/python manage.py clearsessions &>> /usr/local/django_projects/podv4/pod/log/cron_clearsessions.log 2>&1
0 4 * * * cd /usr/local/django_projects/podv4 && /home/pod/.virtualenvs/django_pod/bin/python manage.py index_videos --all &>> /usr/local/django_projects/podv4/pod/log/cron_index.log 2>&1
0 5 * * * cd /usr/local/django_projects/podv4 && /home/pod/.virtualenvs/django_pod/bin/python manage.py check_obsolete_videos >> /usr/local/django_projects/podv4/pod/log/cron_obsolete.log 2>&1
* * * * * cd /usr/local/django_projects/podv4 && /home/pod/.virtualenvs/django_pod/bin/python manage.py live_viewcounter >> /usr/local/django_projects/podv4/pod/log
```
