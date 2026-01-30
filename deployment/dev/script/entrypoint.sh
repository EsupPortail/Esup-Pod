#!/bin/bash
set -e

# ==========================================================
# Django Docker Entrypoint
#
# Features:
#   - Real-time log streaming
#   - Error output capture for final reporting
#   - Clear separation between shell orchestration and Python logic
# ==========================================================

# --- Configuration ---
export EXPOSITION_PORT=${EXPOSITION_PORT:-8000}
export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
export DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
export DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}

# --- Logging helpers ---
log() {
    echo -e "\033[1;34m[Docker-Setup]\033[0m $1"
}

error() {
    echo -e "\033[1;31m[Docker-Error]\033[0m $1" >&2
}

# --- Functions ---

wait_for_db() {
    log "Waiting for the database..."

    if ! python3 deployment/dev/script/wait_for_db.py \
        2> >(tee /tmp/wait_for_db.err >&2); then
        error "Database connection failed."
        error "$(cat /tmp/wait_for_db.err)"
        exit 1
    fi

    log "Database connected."
}

manage_setup() {
    log "Running Django setup..."

    if ! python3 deployment/dev/script/manage_setup.py \
        2> >(tee /tmp/manage_setup.err >&2); then
        error "Django setup failed."
        error "$(cat /tmp/manage_setup.err)"
        exit 1
    fi

    log "Django setup finished successfully."
}

# --- Main ---

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
