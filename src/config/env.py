import environ
from pathlib import Path

env = environ.Env()

BASE_DIR = Path(__file__).resolve().parents[2]