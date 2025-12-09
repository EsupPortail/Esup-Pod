#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

def main():
    base_path = Path(__file__).resolve().parent
    sys.path.append(str(base_path / "src"))

    # Chargement des variables d'environnement depuis .env
    try:
        from dotenv import load_dotenv
        env_path = base_path / '.env'
        load_dotenv(env_path)
    except ImportError:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

    # Import du settings pour récupérer USE_DOCKER
    try:
        from django.conf import settings
        import django
        django.setup()
        use_docker = getattr(settings, "USE_DOCKER", False)
    except Exception:
        use_docker = False  # fallback

    # Gestion du runserver avec host/port par défaut
    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        server_arg_supplied = any(not arg.startswith("-") for arg in sys.argv[2:])
        if not server_arg_supplied:
            host = "0.0.0.0" if use_docker else "127.0.0.1"
            sys.argv.append(f"{host}:8000")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
