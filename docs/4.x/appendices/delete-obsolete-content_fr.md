---
layout: default
version: 4.x
lang: fr
---

# Suppression de contenus obsolètes dans Pod

Si votre serveur Esup-Pod fonctionne depuis longtemps, il peut arriver que certains fichiers soit présents sur le disque mais ne correspondent plus à des vidéos existantes en base de donnée.

Afin de réaliser cette tâche, un script a été réalisé (commande `clean_video_files`).

| Script                                             |
|----------------------------------------------------|
| pod/video/management/commands/clean_video_files.py |
{: .table .table-striped}

Il suffit alors de se positionner dans le bon environnement :

```bash
cd /usr/local/django_projects/podv4/
workon django_pod4
```

En la lancant sans paramètres, elle va parcourir l'ensemble des fichiers vidéos de votre serveur et automatiquement supprimer celles qui ne sont pas liées à un élément "vidéo" :

```bash
python manage.py clean_video_files
```

A partir de la version 3.2 d'Esup-Pod, la commande accepte un argument `--type` qui permet de choisir si on souhaite supprimer les vidéos (valeur par défaut), les userfolders, ou les 2 (all).

Exemple de commandes :

```bash
python manage.py clean_video_files --type=userfolder --dry

python manage.py clean_video_files --type=all --dry
```

Le paramettre `--dry` permet de faire une passe de simulation, juste pour connaitre la liste de ce qui serait supprimé sans qu'il supprime réellement.
Vérifier la liste des éléments à supprimer, puis relancez la commande en supprimant le paramètre "–dry" pour qu'il supprime définitivement les contenus indiqués.
