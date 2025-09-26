---
layout: default
version: 4.x
lang: fr
---

# Importer en masse des utilisateurs d’un Pod vers un autre Pod

1. Exporter les utilisateurs de Pod n°1 :

    Depuis le compte pod :

    ```bash
    python manage.py dumpdata auth.user --indent 2 > export_user.json
    ```

2. Nettoyage du json avec jq :

    Installation de jq depuis debian :

    ```bash
    apt-get install jq
    ```

    ```bash
    cat export_user.json | jq ' [.[] | del(.pk?, .fields.is_superuser?, .fields.last_login?, .fields.date_joined?,
    .fields.groups?, .fields.user_permissions?) ]' > import_user.json
    ```

    Suppression du pk, is_superuser, last-login, ... : à adapter suivant le besoin

3. Import des utilisateurs dans Pod n°2 :

    ```bash
    python manage.py loaddata import_user.json
    ```

    Le pk des users est régénéré à la suite des utilisateurs déjà présents dans votre pod.

> ⚠️ Ces commandes sont peut-être à adapter selon votre environnement.
