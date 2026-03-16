"""
Environment configuration module.

Initializes the `django-environ` environment to handle configuration variables.
Defines the project's base directory (`BASE_DIR`) and loads settings from the
`.env` file if it exists, ensuring seamless configuration management.
"""
from pathlib import Path

import environ

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parents[2]
DOTENV_FILE = BASE_DIR / ".env"

if DOTENV_FILE.is_file():
    env.read_env(str(DOTENV_FILE))
