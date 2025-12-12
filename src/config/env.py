import environ
from pathlib import Path

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parents[2]
DOTENV_FILE = BASE_DIR / ".env"

if DOTENV_FILE.is_file():
    env.read_env(str(DOTENV_FILE))