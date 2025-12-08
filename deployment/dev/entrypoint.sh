#!/bin/bash
set -e

MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-3306}
MARKER_FILE=${MARKER_FILE:-/app/.setup_done}
EXPOSITION_PORT=${EXPOSITION_PORT:-8000}

# Variables pour le superuser par défaut (modifiables via docker-compose)
DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}

wait_for_db() {
    echo "[Docker] Waiting for the database ($MYSQL_HOST:$MYSQL_PORT)..."
    while ! nc -z "$MYSQL_HOST" "$MYSQL_PORT"; do
        sleep 1
    done
    echo "[Docker] Database connected."
}

check_and_run_setup() {
    # On exécute les migrations à chaque démarrage pour être sûr que la DB est à jour
    echo "[Docker] Applying migrations..."
    python manage.py migrate --noinput

    # Création intelligente du superuser sans blocage interactif
    echo "[Docker] Checking/Creating superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD');
    print('Superuser created.');
else:
    print('Superuser already exists.');
"

    # Marqueur optionnel si vous voulez exécuter des choses une seule fois
    if [ ! -f "$MARKER_FILE" ]; then
        touch "$MARKER_FILE"
        echo "[Docker] First launch setup completed."
    fi
}

wait_for_db

if [ "$1" = "run-server" ]; then
    check_and_run_setup
    echo "[Docker] Starting Django server on port $EXPOSITION_PORT..."
    exec python manage.py runserver 0.0.0.0:"$EXPOSITION_PORT"

elif [ "$1" = "shell-mode" ]; then
    echo "[Docker] Interactive Shell mode."
    exec /bin/bash

else
    exec "$@"
fi