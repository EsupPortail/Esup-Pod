---
layout: default
version: 4.x
lang: en
---

# Bulk import users from one Pod to another Pod

1. Export users from Pod #1:

    From the Pod account:

    ```bash
    python manage.py dumpdata auth.user --indent 2 > export_user.json
    ```

2. Clean up the json with jq:

    Install jq from Debian:

    ```bash
    apt-get install jq
    ```

    ```bash
    cat export_user.json | jq ' [.[] | del(.pk?, .fields.is_superuser?, .fields.last_login?, .fields.date_joined?,
    .fields.groups?, .fields.user_permissions?) ]' > import_user.json
    ```

    Deleting pk, is_superuser, last-login, etc.: adapt as needed

3. Importing users into Pod No. 2:

    ```bash
    python manage.py loaddata import_user.json
    ```

    The users' pk is regenerated based on the users already present in your pod.

> ⚠️ These commands may need to be adapted to your environment.
