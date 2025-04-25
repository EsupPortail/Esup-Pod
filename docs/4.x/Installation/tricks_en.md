---
layout: default
version: 4.x
lang: en
---

# Tips and Tricks

## Tip #1: Issue related to flatpages

During tests or migration, you may encounter an error like this:

> django.db.migrations.exceptions.NodeNotFoundError: Migration main.0001_initial dependencies reference nonexistent parent node ('flatpages', '0001_initial')

You should know that the management of static pages is done via a Django flatpages application.
Since this application is not specific to Esup-Pod, its installation directory is located directly in the virtual environment.
Typically, _depending on your version of Python and your virtual environment_, it is:

> /home/pod/.virtualenvs/django_pod4/lib/python3.11/site-packages/django/contrib/flatpages

### Case 1: Issue during the initial creation of the database

If you run the following command multiple times, deleting the database data, via:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ make createDB
```

This should no longer happen because, since Esup-Pod v4, _make createDB_ now runs the following command to delete the flatpages migration files, in addition to the Pod applications:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py delete_flatpages_migrations.py
```

> ⚠️ Be careful not to run this command without understanding the consequences.

### Case 2: Issue during unit tests

If you are developing Esup-Pod and encounter this error during unit tests, for example via:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ python manage.py test pod.video.tests --settings=pod.main.test_settings
```

This is likely due to the configuration of the **USE_DOCKER** parameter.

If you are in a non-containerized environment, please add the following to your settings_local.py:

```conf
USE_DOCKER = false
```

## Tip #2: Issue with django-chunked-upload

If you encounter an issue with the _django-chunked-upload_ application, do not hesitate to run the following commands:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ pip uninstall django-chunked-upload
(django_pod4) pod@pod:~/django_projects/podv4$ pip install -r requirements.txt
```

## Tip #3: Issue with django-shibboleth-remoteuser

If you encounter an issue with the _django-shibboleth-remoteuser_ application, do not hesitate to run the following commands:

```sh
(django_pod4) pod@pod:~/django_projects/podv4$ pip uninstall django-shibboleth-remoteuser
(django_pod4) pod@pod:~/django_projects/podv4$ pip install -r requirements.txt
```
