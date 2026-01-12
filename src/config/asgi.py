import os
import sys
from django.core.asgi import get_asgi_application
from config.env import env

try:
    settings_module = env.str("DJANGO_SETTINGS_MODULE")

    if not settings_module:
        raise ValueError("DJANGO_SETTINGS_MODULE is set but empty.")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    application = get_asgi_application()

except Exception as e:
    print(
        f"FATAL ERROR: Failed to initialize the ASGI application. "
        f"Check that DJANGO_SETTINGS_MODULE is set. Details: {e}",
        file=sys.stderr
    )
    sys.exit(1)
