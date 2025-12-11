import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Use local settings as the default environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.dev.local")  
application = get_wsgi_application()