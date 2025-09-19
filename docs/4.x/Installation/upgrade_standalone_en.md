---
layout: default
version: 4.x
lang: en
---

# Esup-Pod v4 update

## Before an update

### Announce the upgrade to users

In Pod administration (https://VOTRE_SERVEUR/admin/main/configuration/), you’ll find:

The “maintenance_text_scheduled” field lets you define a customized maintenance message.
The “maintenance_scheduled” field lets you display/hide (=1 / 0) this message on Pod.

### D-Day

Switch to maintenance mode (maintenance_mode = 1), this will disable certain functions, and display a “Maintenance in progress. Some features are unavailable”.

## General update commands

### Via makefile

```sh
pod@pod:~$ cd django_projects/podv4/
pod@pod:~/django_projects/podv4$ workon django_pod4
(django_pod4) pod@pod:~/django_projects/podv4$ make upgrade
(django_pod4) pod@pod:~/django_projects/podv4$ sudo systemctl restart uwsgi-pod
```

### Via commands

```sh
pod@pod:~$ cd django_projects/podv4/
pod@pod:~/django_projects/podv4$ workon django_pod4
(django_pod4) pod@pod:~/django_projects/podv4$ git status
(django_pod4) pod@pod:~/django_projects/podv4$ git pull origin main
(django_pod4) pod@pod:~/django_projects/podv4$ pip3 install -r requirements.txt
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py makemigrations
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py migrate
# mise à jour des composants js/css via yarn
(django_pod4) pod@pod:~/django_projects/podv4$ cd pod; yarn upgrade; cd ..
# Attention : avant de lancer collectstatic --clear, assurez-vous d’avoir sauvegardé le dossier static/custom si vous y avez mis des fichiers personnalisés.
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py collectstatic --no-input --clear
(django_pod4) pod@pod:~/django_projects/podv4$ sudo systemctl restart uwsgi-pod
```

When executing the command `make statics` (equivalent to `python manage.py collectstatic --no-input --clear`), if you get an error like `npm@10.8.1: The engine “node” is incompatible with this module. Expected version “^18.17.0 || >=20.5.0”. Got “18.12.1”`, this is due to the NodeJS version.

Simply update NodeJS with the following command (to be adapted to your environment):

```sh
sudo apt install nodejs
```

### Update settings

After updating Esup-Pod, the command below shows the new parameters compared with a previous version:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py compareconfiguration *REVIEW_VERSION*
```

for example, the command

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py compareconfiguration 4.0.0
```

will list all new parameters (and those no longer in use) from 4.0.0 to the current version.

### Database

If you’re upgrading from a version earlier than Pod version 3.3.1 and you’re running MySQL or MariaDB, you’ll need to install the timezone in the SQL engine (as mysql root!).

```sh
podv4$ mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p --database=mysql
```

### Encoding server

Be sure to update your encoding servers!

```sh
pod@pod-encodage:~$ cd django_projects/podv4/
pod@pod-encodage:~/django_projects/podv4$ workon django_pod4
(django_pod4) pod@pod-encodage:~/django_projects/podv4$ git status
(django_pod4) pod@pod-encodage:~/django_projects/podv4$ git pull origin main
(django_pod4) pod@pod-encodage:~/django_projects/podv4$ pip3 install -r requirements.txt
(django_pod4) pod@pod-encodage:~/django_projects/podv4$ sudo /etc/init.d/celeryd restart
```

## Optional - Updating Opencast Studio

To update the Opencast Studio in your Esup-Pod instance, follow these steps:

Go to the `opencast-studio/` folder

Retrieve the latest version of Opencast Studio with the following command:

```sh
# Select a recent tag, as the master branch is on version 2.0, which is a complete redesign.
# tags list: https://github.com/elan-ev/opencast-studio/tags
git checkout tags/2023-09-14
git pull
```

For versions up to 2023-09-14: regenerate Opencast Studio with the correct Pod configuration using the following commands:

```sh
export PUBLIC_URL=/studio
npm install
npm run build
```

For more recent versions (tags > 2023-10-10), the commands differ slightly:

```sh
export PUBLIC_PATH=/studio
npm install
npm run build:release
```

The build directory is now updated. Rename it studio, then copy it to the pod/custom/static/opencast/ directory.

```sh
mkdir -p pod/custom/static/opencast/studio
cp -r build/* pod/custom/static/opencast/studio
```

Finally, don’t forget to collect your static files for production via the command:

```sh
(django_pod) [userpod@video][/data/www/userpod/django_projects/podv2] python manage.py collectstatic
```
