#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
from src.config.env import env
from environ import ImproperlyConfigured

def main():
    """Run administrative tasks."""
    
    base_path = Path(__file__).resolve().parent
    sys.path.append(str(base_path / "src"))

    try:
        settings_module = env.str("DJANGO_SETTINGS_MODULE")
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
        
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
        
    except (ImportError, ImproperlyConfigured) as exc:
        if "django" in str(exc) or isinstance(exc, ImproperlyConfigured):
            msg = (
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment? "
                f"Also check if DJANGO_SETTINGS_MODULE ('{settings_module}') is correctly defined. "
                f"Details: {exc}"
            )
            print(f"FATAL ERROR: {msg}", file=sys.stderr)
            sys.exit(1)
        raise
    except Exception as e:
        print(f"FATAL ERROR during manage.py execution: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()