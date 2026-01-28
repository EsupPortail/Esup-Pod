#!/bin/bash
set -e

# --- Configuration ---
export EXPOSITION_PORT=${EXPOSITION_PORT:-8000}
export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
export DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
export DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}

# --- Functions ---

log() { echo -e "\033[1;34m[Docker-Setup]\033[0m $1"; }
error() { echo -e "\033[1;31m[Docker-Error]\033[0m $1"; }

wait_for_db() {
    log "Waiting for the database..."
    python3 << END
import sys, time
from django.db import connections
from django.db.utils import OperationalError
max_tries = 30
for i in range(max_tries):
    try:
        connections['default'].cursor()
        sys.exit(0)
    except OperationalError:
        time.sleep(1)
sys.exit(1)
END
    if [ $? -eq 0 ]; then
        log "Database connected."
    else
        error "Cannot connect to the database."
        exit 1
    fi
}

manage_setup() {
    log "Starting setup..."

    # 1. Check for missing migrations
    log "Checking migration files..."
    # Attempts to make migrations. If code changed but files haven't, it creates them.
    python manage.py makemigrations --no-input

    # 2. Apply migrations (Critical step)
    log "Applying migrations..."
    if ! python manage.py migrate --noinput; then
        error "MIGRATION FAILED!"
        echo "---------------------------------------------------"
        echo "It seems your database is inconsistent."
        echo "Then restart the server."
        echo "---------------------------------------------------"
        exit 1
    fi

    # 3. Statics
    log "Collecting static files..."
    python manage.py collectstatic --noinput --clear

    # 4. Superuser
    log "Checking Superuser..."
    python manage.py shell << END
import os
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
User = get_user_model()
u = os.environ.get('DJANGO_SUPERUSER_USERNAME')
e = os.environ.get('DJANGO_SUPERUSER_EMAIL')
p = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
print("[Docker-Setup] Checking Superuser...")
if u and p:
    user_qs = User.objects.filter(username=u)
    if not user_qs.exists():
        print(f"[Docker-Setup] Creating superuser: {u}")
        su = User.objects.create_superuser(username=u, email=e, password=p)
    else:
        su = user_qs.first()

    # Ensure superuser has full permissions
    su.is_staff = True
    su.is_superuser = True
    su.save()

    # Dev Setup: Ensure Owner profile is linked to the default site
    # This is required for Pod's multi-site permissions to work correctly in Admin
    from src.apps.authentication.models import Owner
    owner, created = Owner.objects.get_or_create(user=su)
    if Site.objects.exists():
        current_site = Site.objects.first()
        if current_site not in owner.sites.all():
            owner.sites.add(current_site)
            owner.save()
            print(f"[Docker-Setup] Superuser {u} linked to site {current_site.domain}")

    print(f"[Docker-Setup] Superuser {u} ready (is_superuser={su.is_superuser})")
else:
    print("[Docker-Error] Superuser credentials are not fully set.")
END
}

# --- Main ---

wait_for_db

if [ "$1" = "run-server" ]; then
    manage_setup
    log "Starting Django server..."
    exec python manage.py runserver 0.0.0.0:"$EXPOSITION_PORT"
elif [ "$1" = "shell-mode" ]; then
    log "Interactive shell mode."
    exec /bin/bash
else
    exec "$@"
fi
