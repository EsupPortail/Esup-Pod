---
layout: default
version: 4.x
lang: fr
---

# Conseils et astuces

## Astuce #1 : problème en lien avec les flatpages

Lors de tests ou d’une migration, il est possible d’avoir une erreur de ce type :

```log
django.db.migrations.exceptions.NodeNotFoundError: Migration main.0001_initial dependencies reference nonexistent parent node ('flatpages', '0001_initial')
```

Il faut savoir que la gestion des pages statiques se réalise via une application Django flatpages.
Cette application n’étant pas spécifique à Esup-Pod, son répertoire d’installation est situé directement dans l’environnement virtuel.
Typiquement, _selon votre version de Python et votre environnement virtuel_, il s’agit de :

```sh
/home/pod/.virtualenvs/django_pod4/lib/python3.11/site-packages/django/contrib/flatpages
```

### Cas 1 : problème lors de la création initiale de la base de données

Si vous lanciez la commande suivante plusieurs fois, en supprimant les données de la base, via :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ make createDB
```

Cela ne devrait plus arriver car, depuis Esup-Pod v4, _make createDB_ exécute maintenant la commande suivante permettant de supprimer les fichiers de migration des flatpages, en plus des applications de Pod :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py delete_flatpages_migrations.py
```

> ⚠️ Attention à ne lancer cette commande qu’en connaissance de cause.

### Cas 2 : problème lors de lancement de tests unitaires

Si vous développez Esup-Pod et que vous obtenez cette erreur lors de tests unitaires, via par exemple :

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py test pod.video.tests --settings=pod.main.test_settings
```

Cela vient vraisemblablement de la configuration du paramètre **USE_DOCKER**.

Si vous êtes dans un environnement non conteneurisé, veuillez mettre dans votre settings_local.py :

```conf
USE_DOCKER = false
```

## Astuce #2 : problème avec django-chunked-upload

Si vous rencontrez un problème avec l’application _django-chunked-upload_, il ne faut pas hésiter à lancer les commandes suivantes

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ pip uninstall django-chunked-upload
(django_pod4) pod@pod:~/django_projects/podv4$ pip install -r requirements.txt
```

## Astuce #3 : problème avec django-shibboleth-remoteuser

Si vous rencontrez un problème avec l’application _django-shibboleth-remoteuser_, il ne faut pas hésiter à lancer les commandes suivantes

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ pip uninstall django-shibboleth-remoteuser
(django_pod4) pod@pod:~/django_projects/podv4$ pip install -r requirements.txt
```
