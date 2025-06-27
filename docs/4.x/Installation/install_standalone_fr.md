---
layout: default
version: 4.x
lang: fr
---

# Installation d’Esup-Pod en mode Stand Alone

## Environnement

### Création de l’utilisateur Pod

```sh
user@pod:~$  sudo adduser pod
user@pod:~$  adduser pod sudo
user@pod:~$  su pod
user@pod:~$  cd /home/pod
```

### Installation de paquets

```sh
pod@pod:~$ sudo apt-get install git curl vim
```

### Création de l’environnement virtuel

```sh
# Vérifier la version de python
pod@pod:~$ sudo python3 -V
# Pod v4.0 est compatible avec les versions 3.9 à 3.12 de Python.
# Vérifiez aussi le [Statut des versions de python](https://devguide.python.org/versions/) pour ne pas vous appuyer sur une version obsolète.
pod@pod:~$ sudo apt-get install -y python3-pip
pod@pod:~$ sudo pip3 install virtualenvwrapper
```

Depuis python 3.10, il n’est plus possible d’installer avec pip en dehors d’un environnement. Pour pouvoir installer _virtualenvwrapper_ il faut ajouter à la fin de la ligne **--break-system-packages**

À la fin du .bashrc, il faut ajouter ces lignes :

```sh
pod@pod:~$ vim .bashrc
      [..]
      export WORKON_HOME=$HOME/.virtualenvs
      export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
      source /usr/local/bin/virtualenvwrapper.sh
      [..]
```

Puis prendre en charge ces modifications :

```sh
pod@pod:$ source .bashrc
```

Et enfin créez l‘environnement virtuel :

```sh
pod@pod:~$ mkvirtualenv --system-site-packages --python=/usr/bin/python3 django_pod4
```

### Récupération des sources

Concernant l’emplacement du projet, je conseille de le mettre dans _/usr/local/django_projects_

```sh
(django_pod4)pod@pod:~$ sudo mkdir /usr/local/django_projects
```

Vous pouvez faire un lien symbolique dans votre home pour arriver plus vite dans le répertoire _django_projects_ :

```sh
(django_pod4)pod@pod:~$ ln -s /usr/local/django_projects django_projects
```

Placez-vous dans le répertoire django_projects

```sh
(django_pod4)pod@pod:~$ cd django_projects
```

Donnez les droits à l’utilisateur pod de lire et d‘écrire dans le répertoire :

```sh
(django_pod4) pod@pod:~/django_projects$ sudo chown pod:pod /usr/local/django_projects
```

Vous pouvez enfin récupérer les sources

> **Remarque**
>
> Si vous devez utiliser un proxy, vous pouvez le spécifier avec cette commande :
>
> ```sh
> (django_pod4) pod@pod:~/django_projects$ git config --global http.proxy http://PROXY:PORT
> ```

La récupération des sources de la v4 se fait via cette commande :

```sh
(django_pod4) pod@pod:~/django_projects$ git clone https://github.com/EsupPortail/Esup-Pod.git podv4
Clonage dans "podv4"...
remote: Counting objects: 4578, done.
remote: Compressing objects: 100% (378/378), done.
remote: Total 4578 (delta 460), reused 564 (delta 348), pack-reused 3847
Réception d’objets: 100% (4578/4578), 4.40 MiB | 3.88 MiB/s, fait.
Résolution des deltas: 100% (3076/3076), fait.

(django_pod4) pod@pod:~/django_projects$ cd podv4/
```

### Fichier de configuration `settings_local.py`

Vous devez créer un fichier de configuration local dans le dossier `pod/custom`.

Indiquez dans ce fichier uniquement les variables dont vous voulez changer la valeur par défaut. Vous trouverez ci-dessous un exemple de fichier avec les principales variables à modifier : connexion à la base de données, un fichier CSS custom, retirer le langage nl, etc. Vous pouvez adapter ce fichier et le coller dans le vôtre.

```sh
(django_pod4) pod@Pod:~/django_projects/podv4$ vim pod/custom/settings_local.py
```

```py
"""Django local settings for pod_project.Django version : 4.2"""

##
# The secret key for your particular Django installation.
#
# This is used to provide cryptographic signing,
# and should be set to a unique, unpredictable value.
#
# Django will not start if this is not set.
# https://docs.djangoproject.com/fr/4.2/ref/settings/#secret-key
#
# SECURITY WARNING: keep the secret key used in production secret!
# You can visit https://djecrety.ir/ to get it
SECRET_KEY = "A_CHANGER"

##
# DEBUG mode activation
#
# https://docs.djangoproject.com/fr/4.2/ref/settings/#debug
#
# SECURITY WARNING: MUST be set to False when deploying into production.
DEBUG = True

##
# A list of strings representing the host/domain names
# that this Django site is allowed to serve.
#
# https://docs.djangoproject.com/fr/4.2/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost"]

##
# A tuple that lists people who get code error notifications
#   when DEBUG=False and a view raises an exception.
#
# https://docs.djangoproject.com/fr/4.2/ref/settings/#std:setting-ADMINS
#
ADMINS = (
    ("Name", "adminmail@univ.fr"),
)

##
# Internationalization and localization.
#
# https://docs.djangoproject.com/fr/4.2/topics/i18n/
# https://github.com/django/django/blob/master/django/conf/global_settings.py
LANGUAGES = (
    ("fr", "Français"),
    ("en", "English")
)

# Hide Users in navbar
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
# https://docs.djangoproject.com/fr/4.2/ref/settings/#email-host
# https://docs.djangoproject.com/fr/4.2/ref/settings/#email-port
# https://docs.djangoproject.com/fr/4.2/ref/settings/#default-from-email
#
#   username: EMAIL_HOST_USER
#   password: EMAIL_HOST_PASSWORD
#
EMAIL_HOST = "smtp.univ.fr"
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = "noreply@univ.fr"

# https://docs.djangoproject.com/fr/4.2/ref/settings/#std:setting-SERVER_EMAIL
SERVER_EMAIL = "noreply@univ.fr"

##
# THIRD PARTY APPS OPTIONNAL
#
USE_PODFILE = True

##
# TEMPLATE Settings
#
TEMPLATE_VISIBLE_SETTINGS = {
    "TITLE_SITE": "Esup.Pod",
    "TITLE_ETB": "Consortium Esup",
    "LOGO_SITE": "img/logoPod.svg",
    "LOGO_COMPACT_SITE": "img/logoPod.svg",
    "LOGO_ETB": "img/logo_etb.svg",
    "LOGO_PLAYER": "img/logoPod.svg",
    "FOOTER_TEXT": (
        "La Maison des Universités 103 Bvd St Michel",
        "75005  PARIS - France"
    ),
    "LINK_PLAYER": "http://www.univ.fr",
    "CSS_OVERRIDE": "custom/mycss.css",
    "PRE_HEADER_TEMPLATE": ""
}

##
# A string representing the time zone for this installation. (default=UTC)
#
# https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE = "Europe/Paris"
```

## Applications tierces

### Installation de toutes les librairies python

Il faut vérifier que l’on se trouve bien dans l’environnement virtuel (présence de `(django_pod4)` au début l’invite de commande. Sinon, il faut lancer la commande `$> workon django_pod4`

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ pip3 install -r requirements.txt
```

De même, si vous devez utiliser un proxy :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ pip3 install --proxy="PROXY:PORT" -r requirements.txt
```

### FFMPEG

Pour l’encodage des vidéos et la creation des vignettes, il faut installer ffmpeg, ffmpegthumbnailer et imagemagick (ne pas installer sur le serveur frontal si vous déportez l’encodage)

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt install ffmpeg ffmpegthumbnailer imagemagick
```

### Redis

Voir la doc officielle <https://redis.io/docs/getting-started/>

Pour installer le cache Redis

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt install redis-server
```

En théorie le service démarre automatiquement. Si vous avez installé Redis sur la même machine que Pod, rien à faire de plus. Pour vérifier si le service est bien démarré :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo service redis-server status
```

Si vous utilisez Redis sur une autre machine, n’oubliez pas de modifier le bind dans le fichier de configuration _/etc/redis/redis.conf_

> Dans ce cas là, pensez également à vérifier la valeur de `protected-mode` dans le fichier de configuration _/etc/redis/redis.conf_
>
> Soit mettre _protected-mode no_ (et comprendre ce que cela implique) soit mettre _protected-mode yes_ et réaliser la gestion nécessaire vis-à-vis d'un mot de passe pour Redis.
>
> Si _protected-mode yes_ sans mot de passe, vous obtiendrez une erreur du type : `consumer: Cannot connect to redis://:6379/: Error 111 connecting to :6379. Connection refused`
{: .alert .alert-warning}

Si vous ne souhaitez pas toucher au bind, vous pouvez aussi modifier votre `settings_local.py` et personnaliser cette extrait du _settings.py_ par défaut avec votre `<my_redis_host>`

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

### Elasticsearch

Selon la version d’Elasticsearch que vous allez utiliser, les versions des dépendances peuvent changer. Les versions 6 et 7 ne sont actuellement plus maintenues. Par défaut, Pod v4.0 fonctionne avec la version 8 d’Elasticsearch.

#### Elasticsearch 8

Pour utiliser Elasticsearch 8, il faut avoir java 17 sur sa machine.

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt-get install default-jdk
```

Puis pour installer Elasticsearch sur Debian en utilisant les paquets, il faut suivre les instructions situées à cette adresse : <https://www.elastic.co/guide/en/elasticsearch/reference/current/deb.html>.

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
 OK
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt-get install apt-transport-https
(django_pod4) pod@pod:~/django_projects/podv4$ echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt-get update && sudo apt-get install elasticsearch
```

Ensuite il faut paramétrer l’instance :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo vim /etc/elasticsearch/elasticsearch.yml
```

Puis préciser ces valeurs :

```yml
cluster.name: pod-application
node.name: pod-1
discovery.seed_hosts: ["127.0.0.1"]
cluster.initial_master_nodes: ["pod-1"]
```

**Il est recommandé d’utiliser le mode security d’ES8.**
Générer l’utilisateur pod pour ES :

```sh
sudo /usr/share/elasticsearch/bin/elasticsearch-users useradd pod -p podpod -r superuser
```

Génération des certificats (CA + cert) :

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

Dans _/etc/elasticsearch/elasticsearch.yml_ :

```yml
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.verification_mode: certificate
xpack.security.http.ssl.keystore.path: /etc/elasticsearch/elastic-certificates.p12
xpack.security.http.ssl.truststore.path: /etc/elasticsearch/elastic-certificates.p12
```

#### Lancement et vérification d’Elasticsearch

Il faut enfin le lancer et vérifier son bon fonctionnement :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo /etc/init.d/elasticsearch start
(django_pod4) pod@pod:~/django_projects/podv4$ curl -XGET "127.0.0.1:9200"
ou pour ES8
(django_pod4) pod@pod:~/django_projects/podv4$ curl -k -XGET "https://127.0.0.1:9200" -u pod:podpod
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

Pour utiliser la recherche dans Pod, nous allons avoir besoin également du plugin ICU :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ cd /usr/share/elasticsearch/
(django_pod4) pod@pod:/usr/share/elasticsearch$ sudo bin/elasticsearch-plugin install analysis-icu
-> Downloading analysis-icu from elastic
[=================================================] 100%
-> Installed analysis-icu
(django_pod4) pod@pod:/usr/share/elasticsearch$ sudo /etc/init.d/elasticsearch restart
[ ok ] Restarting elasticsearch (via systemctl): elasticsearch.service.
```

Si vous êtes derrière un proxy :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ cd /usr/share/elasticsearch/
(django_pod4) pod@pod:/usr/share/elasticsearch$ sudo CLI_JAVA_OPTS="-Dhttp.proxyHost=proxy.univ.fr -Dhttp.proxyPort=3128 -Dhttps.proxyHost=proxy.univ.fr -Dhttps.proxyPort=3128" /usr/share/elasticsearch/bin/elasticsearch-plugin install analysis-icu
 -> Downloading analysis-icu from elastic
[=================================================] 100%
-> Installed analysis-icu
(django_pod4) pod@pod:/usr/share/elasticsearch$ sudo /etc/init.d/elasticsearch restart
[ ok ] Restarting elasticsearch (via systemctl): elasticsearch.service.
```

#### Création de l’index Pod

> Si vous utilisez elasticsearch 7, vous devez :
> Définir `ES_VERSION = 7` dans votre fichier `settings` et modifier la version du client elasticsearch dans votre fichier `requirements.txt`.
>
> ```conf
> elasticsearch==7.17.9
> ```
>
> Et ne pas oublier de relancer
>
> ```sh
> (django_pod4) pod@podv4:~/django_projects/podv4$ pip3 install -r requirements.txt
> ```

Nous pouvons enfin vérifier le bon fonctionnement de l’ensemble (l’erreur affichée lors de la suppression est normale puisque l’indice n’existe pas, mais nous devons supprimer avant de créer un index dans ES) :

```sh
(django_pod4) pod@pod:/usr/share/elasticsearch$ cd ~/django_projects/podv4
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py create_pod_index
DELETE http://127.0.0.1:9200/pod [status:404 request:0.140s]
An error occured during index video deletion: 404-index_not_found_exception : no such index
Successfully create index Video
(django_pod4) pod@pod:~/django_projects/podv4$ curl -XGET "127.0.0.1:9200/pod/_search"
{"took":35,"timed_out":false,"_shards":{"total":2,"successful":2,"skipped":0,"failed":0},"hits":{"total":0,"max_score":null,"hits":[]}}
```

Si la commande python ne fonctionne pas, créez d’abord l’index à la main avec un `curl  -XPUT "http://127.0.0.1:9200/pod"` (options `-k --noproxy -u <user>:<pwd>` à prévoir si ES8 en mode security)

Si vous déportez elasticsearch sur une autre machine, rajoutez dans le fichier `settings_local.py` son URL d’accès :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ vim pod/custom/settings_local.py
```

Copiez la ligne suivante :

```py
ES_URL = ["http://elastic.domaine.fr:9200/"]
```

Avec le mode security et ES8, vous devrez paramétrer les éléments suivants dans votre settings_local.py :

```py
ES_URL = ["https://127.0.0.1:9200/"] # ou votre instance déportée
ES_OPTIONS = {"verify_certs": False, "basic_auth": ("es_user", "password")}
ES_VERSION = "8"
```

### Installation des dépendances

Pour installer les dépendances, il faut en premier installer nodejs, npm et yarn. L’installation ne fonctionne pas avec nodejs 12.x

La référence est ici : <https://github.com/nodesource/distributions>

#### Debian

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt-get update
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt-get install -y ca-certificates curl gnupg
(django_pod4) pod@pod:~/django_projects/podv4$ sudo mkdir -p /etc/apt/keyrings
(django_pod4) pod@pod:~/django_projects/podv4$ curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
(django_pod4) pod@pod:~/django_projects/podv4$ NODE_MAJOR=18 && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
(django_pod4) pod@pod:~/django_projects/podv4$ sudo apt update && sudo apt install -y nodejs
(django_pod4) pod@pod:~/django_projects/podv4$ sudo corepack enable
```

**CentOS**
Alternativement, si vous êtes sur CentOS 8, installez les dépendances nodejs+npm et yarn ainsi :

```sh
root@pod:~/$ dnf module reset nodejs
root@pod:~/$ dnf module enable nodejs:14
root@pod:~/$ dnf module -y update nodejs
root@pod:~/$ yum install nodejs
root@pod:~/$ npm install yarn -g
```

Se placer dans le répertoire où est installé le package.json

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ cd pod
```

Installez les dépendances.

```sh
(django_pod4) pod@pod:~/django_projects/podv4/pod$ yarn
```

Enfin, déployez les fichiers statiques (l'exécution prend plusieurs minutes).

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py collectstatic --no-input --clear
```

## Mise en route

### Base de données SQLite intégrée

Utilisez le script présent à la racine afin de créer les fichiers de migration, puis de les lancer pour créer la base de données SQLite intégrée.

```sh
(django_pod4) pod@Pod:~/django_projects/podv4$ make createDB
```

Vous trouverez l’ensemble des variables disponibles sur cette page :
[LINK TODO] Configuration de la plateforme

### SuperUtilisateur

Il faut créer un premier utilisateur qui aura tous les pouvoirs sur votre instance.

```sh
(django_pod4) pod@Pod:~/django_projects/podv4$ python manage.py createsuperuser
```

## Lancement des tests unitaires

Afin de vérifier que votre instance est opérationnelle, vous pouvez lancer les tests unitaires :

```sh
(django_pod4) pod@Pod:~/django_projects/podv4$ python3 -m pip install -r requirements-dev.txt
(django_pod4) pod@Pod:~/django_projects/podv4$ python manage.py test --settings=pod.main.test_settings
```

## Modules complémentaires

Ce paragraphe a été rédigé pour pod v2.9.x, il est possible que cela ne concerne pas pod v4

Il existe plusieurs modules complémentaires pouvant être ajoutés à pod (enrichissement, diffusion en direct, etc). Pour activer ces modules, il faut ajouter la ligne suivante au `settings_local.py`

```py
##
# THIRD PARTY APPS OPTIONNAL
#
THIRD_PARTY_APPS = ["live", "enrichment"]
```

> Enrichissement
>
> Selon votre paramétrage système, il est possible que les enrichissements renvoient une erreur 403 forbidden.
> Pour éviter ce problème, vous pouvez rajouter cette ligne dans `settings_local.py`
>
> ```py
> FILE_UPLOAD_PERMISSIONS = 0o644 # Octal number
> ```

## Serveur de développement

Le serveur de développement permet de tester vos futures modifications facilement.

N’hésitez pas à lancer le serveur de développement pour vérifier vos modifications au fur et à mesure.

À ce niveau, vous devriez avoir le site en français et en anglais et voir l’ensemble de la page d’accueil.

```sh
(django_pod4) pod@Pod:~/django_projects/podv4$ python3 manage.py runserver @IP/DNS:8080 --insecure
--> exemple : (django_pod4) pod@pod:~/django_projects/podv4$ python manage.py runserver pod.univ.fr:8080 --insecure
```

---

## Attention

> Quand le site est lancé, il faut se rendre dans la partie administration puis dans site pour renseigner le nom de domaine de votre instance de Pod (par défaut `example.com`).
>
> Avant la mise en production, il faut vérifier le fonctionnement de la plateforme dont l’ajout d’une vidéo, son encodage et sa suppression.
{: .alert .alert-warning}

**Attention, pour ajouter une vidéo, il doit y avoir au moins un type de vidéo disponible. Si vous avez correctement peuplé votre base de données avec le fichier initial_data.json vous devez au moins avoir other/autres.**

**il faut vérifier l’authentification CAS, le moteur de recherche etc.**
