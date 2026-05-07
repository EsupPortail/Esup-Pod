#!/bin/bash
set -e

# ==========================================================
# Django Docker Entrypoint
#
# ==========================================================

export EXPOSITION_PORT=${EXPOSITION_PORT:-8000}
export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
export DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.org}
export DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}

log() {
    echo -e "\033[1;34m[Docker-Setup]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[Docker-Error]\033[0m $1" >&2
}

wait_for_db() {
    log "Waiting for the database..."
    if ! python3 deployment/dev/scripts/wait_for_db.py 2> >(tee /tmp/wait_for_db.err >&2); then
        error "Database connection failed."
        error "$(cat /tmp/wait_for_db.err)"
        exit 1
    fi
    log "Database connected."
}

manage_setup() {
    log "Starting Django setup tasks..."

    log "Running migrations..."
    python manage.py makemigrations --no-input
    python manage.py migrate --noinput

    log "Collecting static files..."
    python manage.py collectstatic --noinput --clear

    log "Ensuring superuser and site configuration..."
    if ! python manage.py ensure_superuser 2> >(tee /tmp/ensure_superuser.err >&2); then
        error "Superuser configuration failed."
        error "$(cat /tmp/ensure_superuser.err)"
        exit 1
    fi

    log "Django setup finished successfully."
}

wait_for_db

if [ "$1" = "run-server" ]; then
    manage_setup
    log "Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:"$EXPOSITION_PORT"
elif [ "$1" = "shell-mode" ]; then
    log "Starting interactive shell..."
    exec /bin/bash
else
    exec "$@"
fi
