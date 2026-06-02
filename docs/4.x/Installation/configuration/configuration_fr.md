---
layout: default
version: 4.x
lang: fr
---

# Configuration de la plateforme

Vous pouvez retrouver toutes les variables de configuration de la plateforme Pod à cette adresse : [https://github.com/EsupPortail/Esup-Pod/blob/main/CONFIGURATION_FR.md](https://github.com/EsupPortail/Esup-Pod/blob/main/CONFIGURATION_FR.md)

Les variables sont utilisées par la plateforme pour son fonctionnement. Leurs valeurs peuvent être changées dans votre fichier de configuration `custom/settings_local.py` :

```sh
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py
```

## Exemple de configuration pour TinyMCE

Si vous souhaitez surcharger la configuration initiale de TinyMCE, vous pouvez le faire en modifiant votre `pod/custom/settings_local.py`.

Vous pouvez consulter pour ce site pour réaliser la configuration TinyMCE : [https://www.tiny.cloud/docs/](https://www.tiny.cloud/docs/)

```sh
##
# TinyMCE configuration
# https://www.tiny.cloud/docs/
#
TINYMCE_DEFAULT_CONFIG = {
    "height": 500,
    "width": "100%",
    "menubar": "file edit view insert format tools",
    "plugins": """
        link code preview charmap table
    """,
    "toolbar": """
        undo redo | bold italic underline |
        alignleft aligncenter alignright | link image media |
        code preview
    """,
    "menu": {
        "view": {"title": "View", "items": "preview code | visualaid"},
        "tools": {"title": "Tools", "items": "link"},
    },
    "link_context_toolbar": True,
    "link_assume_external_targets": "https://",
    "branding": False,
    "resize": False,
    "promotion": False,
}
```
