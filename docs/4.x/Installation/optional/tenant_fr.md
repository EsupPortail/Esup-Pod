---
layout: default
version: 4.x
lang: fr
---

# Mise en place de plusieurs tenants

> ⚠️ Documentation à tester sur un Pod v4.

La mise en place de plusieurs tenants sur votre application Pod permettra d'héberger 2 instances de Pod tout en n'ayant qu'une seule installation de Pod. Vous pourrez donc avoir un `pod1.univ.fr` et un `pod2.univ.fr`. Chaque instance possédera ses propres utilisateurs, ses propres vidéos et ses propres paramètres.

## Pré-configuration dans Pod

Avant de mettre en place à proprement parler le multi-tenants, vous devez vous assurer de correctement configurer vos sites dans votre espace d'administration.

Un "site" dans Django est l'équivalent d'un tenant. Chaque objet site est relié à un nom de domaine, un nom et un identifiant unique.

Dans l'administration des sites (`Administration > Sites > Site`), vous devez donc créer un second site (ou plus, selon vos besoins) qui possédera son propre nom de domaine.

## Déploiement avec Nginx

Afin de mettre en place le multi-tenants sur Pod, il conviendra de correctement paramétrer son serveur Nginx. Plusieurs tenants vont donc signifier plusieurs processus uwsgi, un par tenant.

Ainsi, il suffit de prendre la documentation d'installation de Pod dans la section "Mise en production" et de refaire la manipulation autant de fois que vous avez de sites.

Lors de la mise en place du deuxième site, il conviendra de renommer les fichiers nécessaires à la configuration Nginx avec des noms différents de ceux du premier site. Par exemple :

```bash
pod@pod:~/django_projects/podv4$ cp pod_nginx.conf pod/custom/pod_nginx2.conf
pod@pod:~/django_projects/podv4$ vim pod/custom/pod_nginx2.conf
pod@pod:~/django_projects/podv4$ sudo ln -s /usr/local/django_projects/podv4/pod/custom/pod_nginx2.conf /etc/nginx/sites-enabled/pod_nginx2.conf
pod@pod:~/django_projects/podv4$ sudo /etc/init.d/nginx restart
pod@pod:~/django_projects/podv4$ cp pod_uwsgi.ini pod_uwsgi2.ini
pod@pod:~/django_projects/podv4$ cp pod_uwsgi2.ini pod/custom/.
pod@pod:~/django_projects/podv4$ sudo uwsgi --ini pod/custom/pod_uwsgi2.ini --enable-threads --daemonize /usr/local/django_projects/podv4/pod/log/uwsgi-pod2.log --uid pod2 --gid www-data --pidfile /tmp/pod2.pid
```

### Cas particulier : le fichier `.ini`

Concernant le fichier `pod_uwsgi2.ini`, vous devrez modifier le chemin vers le socket :

```ini
socket = /home/pod/django_projects/podv4/pod4v2.sock
```

Vous devez également utiliser un fichier de settings personnalisé. Pour cela, ajoutez cette ligne à la fin du fichier `.ini` :

```ini
env = DJANGO_SETTINGS_MODULE=pod.sites2_settings
```

### Le fichier de settings

Une fois le déploiement terminé, il est nécessaire de faire quelques ajustements dans le fichier de settings nouvellement créé.

Le fichier doit au minimum contenir ces deux lignes :

```python
from .settings import *
SITE_ID = 2
ES_INDEX = 'pod'
```

Dans ce fichier, il est possible de surcharger n'importe quel setting de Pod pour ce site en particulier.

Exemple d'utilisation :

```bash
python manage.py <commande> --settings=pod.sites2_settings
```

Il est notamment nécessaire de le faire lors de la mise à jour de l'index ElasticSearch.

## Création des "Admin site"

Tout utilisateur ayant le statut **super utilisateur** pourra se connecter sur toutes les instances de Pod déployées.
En revanche, si vous souhaitez avoir des administrateurs de site spécifiques, procédez ainsi :

* Dans l'administration de chaque site, créez un groupe "Admin du site" (ou autre nom au choix) et attribuez-lui les permissions souhaitées.
* Ajoutez les utilisateurs à ce groupe.

Les personnes dans le groupe "Admin du site" n'auront donc les permissions que sur le site du groupe en question.

## Commande de mise en place

Schéma :

```bash
NGINX-VHOST
 -> socket uwsgi
     -> fichier ini uwsgi
         -> fichier de config par tenant (tenant_settings.py)
```

Chaque tenant doit avoir son propre identifiant de site (`SITE_ID=2`).

Exemple de fichier :

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

Paramètres supplémentaires :

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

Chaque commande doit être lancée avec le fichier de settings du tenant :

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
