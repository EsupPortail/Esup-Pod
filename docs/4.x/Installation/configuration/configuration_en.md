---
layout: default
version: 4.x
lang: en
---

# Platform configuration

You can find all the Pod platform configuration variables at this address: [https://github.com/EsupPortail/Esup-Pod/blob/main/CONFIGURATION_EN.md](https://github.com/EsupPortail/Esup-Pod/blob/main/CONFIGURATION_EN.md)

The variables are used by the platform for its operation. Their values can be changed in your configuration file `custom/settings_local.py`:

```sh
(django_pod4) pod@pod:/usr/local/django_projects/podv4$ vim pod/custom/settings_local.py
```

## Example configuration for TinyMCE

If you want to override the default TinyMCE configuration, you can do so by editing your `pod/custom/settings_local.py` file.

You can visit this site for instructions on configuring TinyMCE: [https://www.tiny.cloud/docs/](https://www.tiny.cloud/docs/)

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
