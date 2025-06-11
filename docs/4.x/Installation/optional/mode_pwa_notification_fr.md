---
layout: default
version: 4.x
lang: fr
---

# Mode PWA et notifications

Depuis la version 3.4.0, l'application Esup_pod implémente quelques fonctionnalités des [applications web progressives](https://developer.mozilla.org/fr/docs/Web/Progressive_web_apps), comme l'installation ou les notifications.

## Configuration

Les métadonnées de l'application sont pré-remplies, mais toutes les options (icônes, nom de l'application, etc.) peuvent être surchargées.

Voici la configuration par défaut pour Pod, vous pouvez surcharger chaque variable dans votre fichier de configuration.

```python
PWA_APP_NAME = "Pod"
PWA_APP_DESCRIPTION = _(
"Pod is aimed at users of our institutions, by allowing the publication of "
"videos in the fields of research (promotion of platforms, etc.), training "
"(tutorials, distance training, student reports, etc.), institutional life (video "
"of events), offering several days of content."
)
PWA_APP_THEME_COLOR = "#0A0302"
PWA_APP_BACKGROUND_COLOR = "#ffffff"
PWA_APP_DISPLAY = "standalone"
PWA_APP_SCOPE = "/"
PWA_APP_ORIENTATION = "any"
PWA_APP_START_URL = "/"
PWA_APP_STATUS_BAR_COLOR = "default"
PWA_APP_DIR = "ltr"
PWA_APP_LANG = "fr-FR"
```

Pour en savoir plus : [https://github.com/silviolleite/django-pwa](https://github.com/silviolleite/django-pwa)

## Notifications push

Afin de permettre à l'application d'envoyer aux utilisateurs des notifications natives, il est nécessaire de générer une paire de clés VAPID, par exemple avec des outils tels que [https://web-push-codelab.glitch.me/](https://web-push-codelab.glitch.me/)

Ensuite, les clés doivent être indiqués dans la configuration via les paramètres suivants:

```python
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "<clé-publique>",
    "VAPID_PRIVATE_KEY": "<clé-privée>",
    "VAPID_ADMIN_EMAIL": "contact@example.org"
}
```
