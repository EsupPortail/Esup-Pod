---
layout: default
version: 4.x
lang: fr
---

# Suppression de contenus obsolètes dans Pod

## Suppression des fichiers orphelins

Si votre serveur Esup-Pod fonctionne depuis longtemps, il peut arriver que certains fichiers soient présents sur le disque mais ne correspondent plus à des vidéos existantes en base de donnée.

Afin de réaliser cette tâche, un script a été réalisé (commande `clean_video_files`).

| Script                                             |
|----------------------------------------------------|
| pod/video/management/commands/clean_video_files.py |
{: .table .table-striped}

Il suffit alors de se positionner dans le bon environnement :

```sh
cd /usr/local/django_projects/podv4/
workon django_pod4
```

En la lancant sans paramètres, elle va parcourir l’ensemble des fichiers vidéos de votre serveur et automatiquement supprimer celles qui ne sont pas liées à un élément "vidéo" :

```sh
python manage.py clean_video_files
```

La commande accepte un argument `--type` qui permet de choisir si on souhaite supprimer les vidéos (valeur par défaut), les userfolders, ou les 2 (all).

Exemples de commandes :

```sh
python manage.py clean_video_files --type=userfolder --dry
python manage.py clean_video_files --type=all --dry
```

Le paramettre `--dry` permet de faire une passe de simulation, juste pour connaitre la liste de ce qui serait supprimé sans qu’il supprime réellement.
Vérifier la liste des éléments à supprimer, puis relancez la commande en supprimant le paramètre `-–dry` pour qu’il supprime définitivement les contenus indiqués.

Nous vous invitons à appeler cette commande régulièrement via un cron. Par exemple :

```sh
# Suppressions de fichiers vidéos inutilisés (le 1er du mois)
00 02 1 * * poduser cd /data/www/poduser/django_projects/podv4 && /data/www/poduser/.virtualenvs/django_pod4/bin/python manage.py clean_video_files
```

## Suppression des fragments obsoletes

Cette commande cron vous premettra de nettoyer régulièrement le dossier `chunked_upload` :

```sh
# Suppression des anciens chunks (Chaque dimanche)
04 04 * * 0 poduser find /data/www/poduser/media/chunked_uploads -mtime +14 -delete &>> /var/log/pod/cron_clear_chunks.log 2>&1
```
