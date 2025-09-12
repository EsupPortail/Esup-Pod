---
layout: default
version: 4.x
lang: fr
---

# Relancer la génération de vignettes pour des vidéos

Afin de réaliser cette tâche, un script a été réalisé (commande `create_thumbnail`).

| Script                                           |
|--------------------------------------------------|
| pod/video/management/commands/create_thubnail.py |
{: .table .table-striped}

Il suffit alors de se positionner dans le bon environnement :

```bash
cd /usr/local/django_projects/podv4/
workon django_pod4
```

Et de lancer la commande de régénération :

```bash
python manage.py create_thumbnail video_id1 video_id2
```

Pensez à changer les ids des vidéos dans la commande.
{: .alert .alert-warning}
