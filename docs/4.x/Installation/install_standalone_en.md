---
layout: default
version: 4.x
lang: en
---

# Esup-Pod v4 Stand-alone installation

## Environment

### User creation in Pod

```sh
user@pod:~$  sudo adduser pod
user@pod:~$  adduser pod sudo
user@pod:~$  su pod
user@pod:~$  cd /home/pod
```

### Packages installation

```sh
pod@pod:~$ sudo apt-get install git curl vim
```

### Virtual environment creation

```sh
pod@pod:~$ sudo python3 -V
pod@pod:~$ sudo python -V
pod@pod:~$ sudo apt-get install -y python3-pip
pod@pod:~$ sudo pip3 install virtualenvwrapper
```

Since python 3.10, it is no longer possible to install pip outside an environment. To install _virtualenvwrapper_, you must add **--break-system-packages** at the end of the line.

At the end of the .bashrc file, add these lines:

```sh
pod@pod:~$ vim .bashrc
      [..]
      export WORKON_HOME=$HOME/.virtualenvs
      export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
      source /usr/local/bin/virtualenvwrapper.sh
      [..]
```

Then take over these modifications:

```sh
pod@pod:$ source .bashrc
```

Finally, create the virtual environment:

```sh
pod@pod:~$ mkvirtualenv --system-site-packages --python=/usr/bin/python3 django_pod3
```

## Getting the sources

Regarding the location of the project, I recommend putting it in _/usr/local/django_projects_.

```sh
(django_pod3)pod@pod:~$ sudo mkdir /usr/local/django_projects
```

You can make a symbolic link in your home to get to the _django_projects_ directory faster:

```sh
(django_pod3)pod@pod:~$ ln -s /usr/local/django_projects _django_projects_
```

Go to the django_projects directory

```sh
(django_pod3)pod@pod:~$ cd django_projects
```
Give the pod user rights to read and write the :

```sh
(django_pod3) pod@pod:~/django_projects$ sudo chown pod:pod /usr/local/django_projects
```

Finally, you can retrieve the sources

> Note
> If you need to use a proxy, you can specify it with this command:
>
> ```sh
> (django_pod3) pod@pod:~/django_projects$ git config --global http.proxy http://PROXY:PORT
> ```

To retrieve the V3 sources, use this command: _git clone https://github.com/EsupPortail/Esup-Pod.git podv3_

```sh
(django_pod3) pod@pod:~/django_projects$ git clone https://github.com/EsupPortail/Esup-Pod.git podv3
Cloning in 'podv3'...
remote: Counting objects: 4578, done.
remote: Compressing objects: 100% (378/378), done.
remote: Total 4578 (delta 460), reused 564 (delta 348), pack-reused 3847
Receiving objects: 100% (4578/4578), 4.40 MiB | 3.88 MiB/s, done.
Delta resolution: 100% (3076/3076), done.

(django_pod3) pod@pod:~/django_projects$ cd podv3/
```

# Third-party applications

## Install all python libraries
Check that you are in the virtual environment (presence of “(django_pod3)” at the start of the command prompt. If not, run the command **$> workon django_pod3**.

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ pip3 install -r requirements.txt
```

Similarly, if you need to use a proxy :

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ pip3 install --proxy=“PROXY:PORT” -r requirements.txt
```
## FFMPEG

To encode videos and create thumbnails, you need to install ffmpeg, ffmpegthumbnailer and imagemagick (do not install on the front-end server if you're offshoring encoding).

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt install ffmpeg ffmpegthumbnailer imagemagick
```

## Redis

See the official doc <https://redis.io/docs/getting-started/>

To install the Redis cache

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt install redis-server
```

In theory, the service starts automatically. If you've installed Redis on the same machine as Pod, you don't need to do anything else. To check whether the service has started :

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ sudo service redis-server status
```

If you're using Redis on another machine, don't forget to modify the bind in the _/etc/redis/redis.conf_ configuration file.

If you don't want to change the bind, you can also modify your _settings_local.py_ and customize this extract from the default _settings.py_ with your <my_redis_host>.

```py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://<my_redis_host>:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "pod",
    },
    "select2": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://<my_redis_host>:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}
SESSION_ENGINE = "redis_sessions.session"
SESSION_REDIS = {
    "host": "<my_redis_host>",
    "port": 6379,
    "db": 4,
    "prefix": "session",
    "socket_timeout": 1,
    "retry_on_timeout": False,
}
```
## Elasticsearch

Depending on the version of Elasticsearch you're going to use, the dependency versions may change. Versions 6 and 7 are currently no longer maintained. Version 8 is to be configured below. Version 6 is the default in Pod.

### Elasticsearch 8

To use Elasticsearch 8, you need java 17 on your machine.

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt-get install default-jdk
```

To install Elasticsearch on Debian using packages, follow the instructions at https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html.

You can install Elasticsearch in version 7 (more maintained) or version 8.

Here's how to install ES8:

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
 OK
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt-get install apt-transport-https
(django_pod3) pod@pod:~/django_projects/podv3$ echo “deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main” | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt-get update && sudo apt-get install elasticsearch
```

Next, set up the :
```sh
(django_pod3) pod@pod:~/django_projects/podv3$ sudo vim /etc/elasticsearch/elasticsearch.yml
```
Puis préciser ces valeurs :

```yml
cluster.name : pod-application
node.name : pod-1
discovery.seed_hosts : [« 127.0.0.1 »]
cluster.initial_master_nodes : [« pod-1 »]
```

**Il est recommandé d'utiliser le mode security d'ES8.**
Générer l'utilisateur pod pour ES :

```sh
sudo /usr/share/elasticsearch/bin/elasticsearch-users useradd pod -p podpod -r superuser
```

Génération des certificats (CA + cert) :

```sh
sudo /usr/share/elasticsearch/bin/elasticsearch-certutil ca
sudo /usr/share/elasticsearch/bin/elasticsearch-certutil cert --ca elastic-stack-ca.p12

sudo /usr/share/elasticsearch/bin/elasticsearch-keystore add xpack.security.http.ssl.keystore.secure_password
sudo /usr/share/elasticsearch/bin/elasticsearch-keystore add xpack.security.http.ssl.truststore.secure_password
```

Copier le fichier _.p12_ dans _/etc/elasticsearch/_

```sh
sudo cp /usr/share/elasticsearch/elastic-stack-ca.p12 /usr/share/elasticsearch/elastic-certificates.p12 /etc/elasticsearch/
sudo chown pod:pod /etc/elasticsearch/elastic-stack-ca.p12 /etc/elasticsearch/elastic-certificates.p12
sudo chmod +r /etc/elasticsearch/elastic-stack-ca.p12 /etc/elasticsearch/elastic-certificates.p12
```

Dans _/etc/elasticsearch/elasticsearch.yml_ :

```yml
xpack.security.http.ssl.enabled : true
xpack.security.http.ssl.verification_mode : certificate
xpack.security.http.ssl.keystore.path : /etc/elasticsearch/elastic-certificates.p12
xpack.security.http.ssl.truststore.path : /etc/elasticsearch/elastic-certificates.p12
```
### Launching and checking Elasticsearch

Finally, it's time to launch Elasticsearch and check that it's working properly:
```sh
(django_pod3) pod@pod:~/django_projects/podv3$ sudo /etc/init.d/elasticsearch start
(django_pod3) pod@pod:~/django_projects/podv3$ curl -XGET "127.0.0.1:9200"
ou pour ES8
(django_pod3) pod@pod:~/django_projects/podv3$ curl -k -XGET 'https://127.0.0.1:9200' -u pod:podpod
```

```json
{
 "name": "pod-1",
"cluster_name": "pod-application",
  "cluster_uuid": "5yhs9zc4SRyjaKYyW7uabQ",
  "version": {
    "number": "8.4.0",
    "build_flavor": "default",
    "build_type": "deb",
    "build_hash": "f56126089ca4db89b631901ad7cce0a8e10e2fe5",
    "build_date": "2022-08-19T19:23:42.954591481Z",
    "build_snapshot": false,
    "lucene_version": "9.3.0",
    "minimum_wire_compatibility_version": "7.17.0",
    "minimum_index_compatibility_version": "7.0.0"
  },
  "tagline": "You Know, for Search"
}
```
To use the search in Pod, we will also need the ICU plugin:
```sh
(django_pod3) pod@pod:~/django_projects/podv3$ cd /usr/share/elasticsearch/
(django_pod3) pod@pod:/usr/share/elasticsearch$ sudo bin/elasticsearch-plugin install analysis-icu
-> Downloading analysis-icu from elastic
[=================================================] 100%
-> Installed analysis-icu
(django_pod3) pod@pod:/usr/share/elasticsearch$ sudo /etc/init.d/elasticsearch restart
[ ok ] Restarting elasticsearch (via systemctl): elasticsearch.service.
```

If you are using a proxy :

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ cd /usr/share/elasticsearch/
(django_pod3) pod@pod:/usr/share/elasticsearch$ sudo ES_JAVA_OPTS="-Dhttp.proxyHost=proxy.univ.fr -Dhttp.proxyPort=3128 -Dhttps.proxyHost=proxy.univ.fr -Dhttps.proxyPort=3128" /usr/share/elasticsearch/bin/elasticsearch-plugin install analysis-icu
 -> Downloading analysis-icu from elastic
[=================================================] 100%
-> Installed analysis-icu
(django_pod3) pod@pod:/usr/share/elasticsearch$ sudo /etc/init.d/elasticsearch restart
[ ok ] Restarting elasticsearch (via systemctl): elasticsearch.service.
```

Warning, for ES8 behind a proxy :

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ cd /usr/share/elasticsearch/
(django_pod3) pod@pod:/usr/share/elasticsearch$ sudo CLI_JAVA_OPTS="-Dhttp.proxyHost=proxy.univ.fr -Dhttp.proxyPort=3128 -Dhttps.proxyHost=proxy.univ.fr -Dhttps.proxyPort=3128" /usr/share/elasticsearch/bin/elasticsearch-plugin install analysis-icu
 -> Downloading analysis-icu from elastic
[=================================================] 100%
-> Installed analysis-icu
(django_pod3) pod@pod:/usr/share/elasticsearch$ sudo /etc/init.d/elasticsearch restart
[ ok ] Restarting elasticsearch (via systemctl): elasticsearch.service.
```
### Pod index creation
> To use elasticsearch 7 or 8, you must :
> Add ES_VERSION = 7 or ES_VERSION = 8 to your settings file and modify the elasticsearch client version in the _requirements.txt_ file.
>
> ```
> elasticsearch==8.9.0
> ```
>
> And don't forget to relaunch
>
> ```sh
> (django_pod3) pod@podv3:~/django_projects/podv3$ pip3 install -r requirements.txt
> ```

Finally, we can check that the assembly is working properly (the error displayed when deletion is normal since the index doesn't exist, but we need to delete before creating an index in ES):

```sh
(django_pod3) pod@pod:/usr/share/elasticsearch$ cd ~/django_projects/podv3
(django_pod3) pod@pod:~/django_projects/podv3$ python manage.py create_pod_index
DELETE http://127.0.0.1:9200/pod [status:404 request:0.140s]
An error occured during index video deletion: 404-index_not_found_exception : no such index
Successfully create index Video
(django_pod3) pod@pod:~/django_projects/podv3$ curl -XGET “127.0.0.1:9200/pod/_search”
{“took”:35,“timed_out”:false,“_shards”:{“total”:2,“successful”:2,“skipped”:0,“failed”:0},“hits”:{“total”:0,“max_score”:null,“hits”:[]}}
```

If the python command doesn't work, first create the index by hand with a **curl -XPUT “http://127.0.0.1:9200/pod” (options -k --noproxy -u <user>:<pwd>** to be expected if ES8 in security mode)
If you're moving elastic search to another machine, add its access URL to the _settings_local.py_ file:

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ vim pod/custom/settings_local.py
```

Copy the following line:

```py
ES_URL = ['http://elastic.domaine.fr:9200/']
```

With security mode and ES8, you will need to set the following in your settings_local.py :

```py
ES_URL = ['https://127.0.0.1:9200/'] # or your remote instance
ES_OPTIONS = { 'verify_certs': False, 'basic_auth': ('es_user', 'password')}
ES_VERSION = “7” or “8
```

## Installing dependencies
To install the dependencies, you must first install nodejs, npm and yarn. Installation does not work with nodejs 12.x

The reference is here: https://github.com/nodesource/distributions

**Debian**
```sh
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt-get update
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt-get install -y ca-certificates curl gnupg
(django_pod3) pod@pod:~/django_projects/podv3$ sudo mkdir -p /etc/apt/keyrings
(django_pod3) pod@pod:~/django_projects/podv3$ curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
(django_pod3) pod@pod:~/django_projects/podv3$ NODE_MAJOR=18 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
(django_pod3) pod@pod:~/django_projects/podv3$ sudo apt update && sudo apt install -y nodejs
(django_pod3) pod@pod:~/django_projects/podv3$ sudo corepack enable
```

**CentOS**
Alternatively, if you are on CentOS 8, install the nodejs+npm and yarn dependencies as follows:

```sh
root@pod:~/$ dnf module reset nodejs
root@pod:~/$ dnf module enable nodejs:14
root@pod:~/$ dnf module -y update nodejs
root@pod:~/$ yum install nodejs
root@pod:~/$ npm install yarn -g
```
Go to the directory where the package.json is installed

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ cd pod
```

Install dependencies.

```sh
(django_pod3) pod@pod:~/django_projects/podv3/pod$ yarn
```

Finally, deploy the static files.

```sh
(django_pod3) pod@pod:~/django_projects/podv3$ python manage.py collectstatic --no-input --clear
```

# Getting started

## Integrated SQLite database

Run the root script to create the migration files, then run them to create the embedded SQLite database.

```sh
(django_pod3) pod@Pod:~/django_projects/podv3$ make createDB
```

_settings_local.py_ configuration file
Create a local configuration file in the _pod/custom_ folder.

This file contains only those variables whose default values you wish to change. Below is an example of a file with the main variables to be modified: database connection, a custom CSS file, pod green theme, remove nl language, etc. You can adapt this file and paste it into your own.

```sh
(django_pod3) pod@Pod:~/django_projects/podv3$ vim pod/custom/settings_local.py
```
```py
"""Django local settings for pod_project.Django version : 3.2"""

##
# The secret key for your particular Django installation.
#
# This is used to provide cryptographic signing,
# and should be set to a unique, unpredictable value.
#
# Django will not start if this is not set.
# https://docs.djangoproject.com/fr/3.2/ref/settings/#secret-key
#
# SECURITY WARNING: keep the secret key used in production secret!
# You can visit https://djecrety.ir/ to get it
SECRET_KEY = 'A_CHANGER'

##
# DEBUG mode activation
#
# https://docs.djangoproject.com/fr/3.2/ref/settings/#debug
#
# SECURITY WARNING: MUST be set to False when deploying into production.
DEBUG = True

##
# A list of strings representing the host/domain names
# that this Django site is allowed to serve.
#
# https://docs.djangoproject.com/fr/3.2/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost']

##
# A tuple that lists people who get code error notifications
#   when DEBUG=False and a view raises an exception.
#
# https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-ADMINS
#
ADMINS = (
    ('Name', 'adminmail@univ.fr'),
)


##
# Internationalization and localization.
#
# https://docs.djangoproject.com/fr/3.2/topics/i18n/
# https://github.com/django/django/blob/master/django/conf/global_settings.py
LANGUAGES = (
    ('fr', 'Français'),
    ('en', 'English')
)

#Hide Users in navbar
HIDE_USER_TAB = True
# Hide Types tab in navbar
HIDE_TYPES_TAB = True
# Hide Tags
HIDE_TAGS = True
# Hide disciplines in navbar
HIDE_DISCIPLINES = True

##
# eMail settings
#
# https://docs.djangoproject.com/fr/3.2/ref/settings/#email-host
# https://docs.djangoproject.com/fr/3.2/ref/settings/#email-port
# https://docs.djangoproject.com/fr/3.2/ref/settings/#default-from-email
#
#   username: EMAIL_HOST_USER
#   password: EMAIL_HOST_PASSWORD
#
EMAIL_HOST = 'smtp.univ.fr'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'noreply@univ.fr'

# https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-SERVER_EMAIL
SERVER_EMAIL = 'noreply@univ.fr'

##
# THIRD PARTY APPS OPTIONNAL
#
USE_PODFILE = True

##
# TEMPLATE Settings
#
TEMPLATE_VISIBLE_SETTINGS = {
    'TITLE_SITE': 'Lille.Pod',
    'TITLE_ETB': 'Université de Lille',
    'LOGO_SITE': 'img/logoPod.svg',
    'LOGO_COMPACT_SITE': 'img/logoPod.svg',
    'LOGO_ETB': 'img/logo_etb.svg',
    'LOGO_PLAYER': 'img/logoPod.svg',
    'FOOTER_TEXT': (
        '42, rue Paul Duez',
        '59000 Lille - France',
        ('<a href="https://goo.gl/maps/AZnyBK4hHaM2"'
            ' target="_blank">Google maps</a>')
    ),
    'LINK_PLAYER': 'http://www.univ-lille.fr',
    'CSS_OVERRIDE': 'custom/mycss.css',
    'PRE_HEADER_TEMPLATE': ''
}

##
# A string representing the time zone for this installation. (default=UTC)
#
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE = 'Europe/Paris'
```
All available variables can be found on this page:
[LINK TODO] Platform configuration

## SuperUser

Create a first user who will have full authority over your instance.

SH
(django_pod3) pod@Pod:~/django_projects/podv3$ python manage.py createsuperuser
```

## Launch unit tests

To check that your instance is operational, you can run the unit tests:

```sh
(django_pod3) pod@Pod:~/django_projects/podv3$ python3 -m pip install -r requirements-dev.txt
(django_pod3) pod@Pod:~/django_projects/podv3$ python manage.py test --settings=pod.main.test_settings
```

## Add-on modules

This paragraph was written for pod v2.9.x; it may not apply to pod v3.

There are several add-on modules that can be added to pod (enrichment, live broadcast, etc.). To activate these modules, add the following line to _settings_local.py_.

```py
##
# THIRD PARTY APPS OPTIONNAL
#
THIRD_PARTY_APPS = ["live", "enrichment"]
```

> Enrichment
>
> Depending on your system settings, enrichments may return a 403 forbidden error.
> To avoid this problem, you can add this line to _settings_local.py_.
>
> ```python
> FILE_UPLOAD_PERMISSIONS = 0o644 # Octal number
> ```
## Development server

The development server makes it easy to test your future modifications.

Don't hesitate to launch the development server to check your modifications as you go along.

At this stage, you should have the site in French and English and be able to see the entire home page.

```sh
(django_pod3) pod@Pod:~/django_projects/podv3$ python3 manage.py runserver @IP/DNS:8080 --insecure
--> example: (django_pod3) pod@pod:~/django_projects/podv3$ python manage.py runserver pod.univ.fr:8080 --insecure
```

---

## Warning

**When the site is launched, go to the administration section and then to site to enter the domain name of your Pod instance (by default 'example.com').

**Before going into production, you need to check that the platform is working properly, including adding, encoding and deleting videos.

**Please note that to add a video, at least one video type must be available. If you have correctly populated your database with the initial_data.json file, you must have at least other/autres.** **.

**CAS authentication, search engine, etc.** must be checked.