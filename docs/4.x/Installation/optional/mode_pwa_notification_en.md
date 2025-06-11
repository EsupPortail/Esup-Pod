---
layout: default
version: 4.x
lang: fr
---

# PWA Mode and notifications

Since version 3.4.0, the Esup_pod application implements some features of [Progressive Web Apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps), such as installation and notifications.

## Configuration

The application metadata is pre-filled, but all options (icons, application name, etc.) can be overridden.

Here is the default configuration for Pod; you can override each variable in your configuration file.

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

For more information: [https://github.com/silviolleite/django-pwa](https://github.com/silviolleite/django-pwa)

## Push notifications

To allow the application to send native notifications to users, it is necessary to generate a pair of VAPID keys, for example, using tools such as [https://web-push-codelab.glitch.me/](https://web-push-codelab.glitch.me/)

Then, the keys must be specified in the configuration via the following parameters:

```python
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "<public-key>",
    "VAPID_PRIVATE_KEY": "<private-key>",
    "VAPID_ADMIN_EMAIL": "contact@example.org"
}
```
