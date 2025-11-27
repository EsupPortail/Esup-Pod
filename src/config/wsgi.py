import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Chargement du .env pour la prod
try:
    from dotenv import load_dotenv
    # On suppose que le .env est à la racine du projet (2 niveaux au-dessus de src/config)
    # Ajuste le chemin selon ton déploiement réel
    env_path = Path(__file__).resolve().parents[2] / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
application = get_wsgi_application()