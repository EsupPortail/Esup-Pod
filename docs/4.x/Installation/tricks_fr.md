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

## Astuce #4 : erreur lors de l’exécution de `make updatedb`

Lors d’une mise à jour de la base de données avec `make updatedb` (ou de la
création de migrations avec `python3 manage.py makemigrations`), une erreur de
ce type peut survenir :

```log
Running migrations:
Applying flatpages.0002_flatpage_content_en_flatpage_content_fr_and_more...Traceback (most recent call last):
...
MySQLdb.OperationalError: (1060, "Duplicate column name 'content_en'")
```

Cette erreur est liée à l’utilisation de l’application Django `flatpages`
lors d’un changement de version de Django.

Pour la corriger :

1. Effectuez une sauvegarde complète de la base de données, ainsi qu’une
   sauvegarde spécifique de la table `django_flatpage`.
2. Dans cette table, supprimez les quatre colonnes concernées :
   `content_en`, `content_fr`, `title_en` et `title_fr`.
3. Supprimez toutes les lignes de la table `django_flatpage`.
4. Relancez `make updatedb`.
5. Réinsérez les lignes de la table à partir de la sauvegarde.

> ⚠️ Ne modifiez pas la table `django_flatpage` sans avoir préalablement
> vérifié vos sauvegardes.

## Astuce #5 : anciens liens de vidéos en mode brouillon invalides

Si les liens d’anciennes vidéos en mode brouillon ne fonctionnent plus après
une migration d’un serveur Esup-Pod v3 vers un serveur v4, cela provient
généralement d’un changement de la valeur de `SECRET_KEY` dans le fichier
`settings_local.py`.

Rétablissez l’ancienne valeur de `SECRET_KEY` pour rendre ces liens de nouveau
fonctionnels.
