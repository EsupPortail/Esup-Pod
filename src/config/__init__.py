try:
    from .django.settings_local import *  # noqa: F401, F403
except ImportError:
    pass
