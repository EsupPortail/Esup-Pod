#!/bin/bash
set -e

MYSQL_HOST=${MYSQL_HOST:-127.0.0.1}
MYSQL_PORT=${MYSQL_PORT:-3306}
MARKER_FILE=${MARKER_FILE:-/app/.setup_done}
EXPOSITION_PORT=${EXPOSITION_PORT:-8000}

wait_for_db() {
    echo "[Docker] Waiting for the database ($MYSQL_HOST:$MYSQL_PORT)..."
    while ! nc -z "$MYSQL_HOST" "$MYSQL_PORT"; do
        sleep 1
    done
    echo "[Docker] Database connected."
}

check_and_run_setup() {
    if [ -f "$MARKER_FILE" ]; then
        echo "[Docker] Setup already completed (file $MARKER_FILE found)."
        echo "[Docker] Starting directly."
    else
        echo "[Docker] First launch detected (or marker missing)."
        echo "[Docker] Running 'make setup'..."
        
        make setup
        
        touch "$MARKER_FILE"
        echo "[Docker] Setup finished and marker created."
    fi
}

wait_for_db

if [ "$1" = "run-server" ]; then
    check_and_run_setup
    echo "[Docker] Starting Django server on port $EXPOSITION_PORT..."
    exec python manage.py runserver 0.0.0.0:"$EXPOSITION_PORT"

elif [ "$1" = "shell-mode" ]; then
    echo "[Docker] Interactive Shell mode."
    if [ ! -f "$MARKER_FILE" ]; then
        echo "---------------------------------------------------------------"
        echo " WARNING: Setup does not seem to have been done."
        echo " Run 'make setup' in this terminal before launching 'make run'."
        echo "---------------------------------------------------------------"
    else
        echo "Setup seems already done. You can run 'make run'."
    fi
    exec /bin/bash

else
    exec "$@"
fi
