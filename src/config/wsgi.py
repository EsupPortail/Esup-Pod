import os
import sys
from django.core.wsgi import get_wsgi_application
from config.env import env 

try:
    settings_module = env.str("DJANGO_SETTINGS_MODULE")

    if not settings_module:
        raise ValueError("DJANGO_SETTINGS_MODULE is set but empty.")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
    application = get_wsgi_application()

except Exception as e:
    print(
        f"FATAL ERROR: Failed to initialize the ASGI application. "
        f"Check that DJANGO_SETTINGS_MODULE is set. Details: {e}", 
        file=sys.stderr
    )
    sys.exit(1)
