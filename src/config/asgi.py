import os
from django.core.asgi import get_asgi_application

# Use local settings as the default environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.dev.local")  
application = get_asgi_application()
