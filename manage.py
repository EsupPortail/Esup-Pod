#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

def main():
    base_path = Path(__file__).resolve().parent
    sys.path.append(str(base_path / "src"))

    if len(sys.argv) > 1 and sys.argv[1] == "runserver":
        server_arg_supplied = any(not arg.startswith("-") for arg in sys.argv[2:])
        if not server_arg_supplied:
            sys.argv.append("0.0.0.0:8000")

    try:
        from dotenv import load_dotenv
        env_path = base_path / '.env'
        load_dotenv(env_path)
    except ImportError:
        pass 

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

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