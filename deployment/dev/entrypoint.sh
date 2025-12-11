#!/bin/bash
set -e

export EXPOSITION_PORT=${EXPOSITION_PORT:-8000}
export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
export DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
export DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}
export DJANGO_ENV=${DJANGO_ENV:-development}


wait_for_db() {
    echo "[Docker] Checking database availability..."
    
    python3 << END
import sys
import time
import os
from django.db import connections
from django.db.utils import OperationalError

connected = False
while not connected:
    try:
        connections['default'].cursor()
        connected = True
    except OperationalError:
        print("[Docker] DB not ready yet, retrying in 1s...")
        time.sleep(1)

sys.exit(0)
END
    echo "[Docker] Successfully connected to the database."
}

manage_setup() {
    echo "[Docker] Starting automatic setup..."

    echo "[Docker] Applying migrations..."
    python manage.py migrate --noinput

    echo "[Docker] Collecting static files..."
    python manage.py collectstatic --noinput --clear

    echo "[Docker] Checking superuser..."
    python manage.py shell << END
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not username or not password:
    print(f"[Django] ERROR: Missing environment variables for the superuser.")
elif not User.objects.filter(username=username).exists():
    print(f"[Django] Creating superuser: {username}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print(f"[Django] Superuser '{username}' already exists. No action taken.")
END
}

wait_for_db

if [ "$1" = "run-server" ]; then
    manage_setup
    echo "[Docker] Starting Django server on port $EXPOSITION_PORT..."
    exec python manage.py runserver 0.0.0.0:"$EXPOSITION_PORT"

elif [ "$1" = "shell-mode" ]; then
    echo "[Docker] Interactive shell mode."
    exec /bin/bash

else
    exec "$@"
fi
