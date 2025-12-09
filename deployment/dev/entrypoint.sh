#!/bin/bash
set -e

export EXPOSITION_PORT=${EXPOSITION_PORT:-8000}
export DJANGO_SUPERUSER_USERNAME=${DJANGO_SUPERUSER_USERNAME:-admin}
export DJANGO_SUPERUSER_EMAIL=${DJANGO_SUPERUSER_EMAIL:-admin@example.com}
export DJANGO_SUPERUSER_PASSWORD=${DJANGO_SUPERUSER_PASSWORD:-admin}
export DJANGO_ENV=${DJANGO_ENV:-development}


wait_for_db() {
    echo "[Docker] Vérification de la disponibilité de la base de données..."
    
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
        print("[Docker] La DB n'est pas encore prête, nouvelle tentative dans 1s...")
        time.sleep(1)

sys.exit(0)
END
    echo "[Docker] Base de données connectée avec succès."
}

manage_setup() {
    echo "[Docker] Début de la configuration automatique..."

    echo "[Docker] Application des migrations..."
    python manage.py migrate --noinput

    echo "[Docker] Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput --clear

    echo "[Docker] Vérification du super utilisateur..."
    python manage.py shell << END
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not username or not password:
    print(f"[Django] ERREUR: Variables d'environnement manquantes pour le superuser.")
elif not User.objects.filter(username=username).exists():
    print(f"[Django] Création du superuser : {username}")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print(f"[Django] Le superuser '{username}' existe déjà. Aucune action.")
END
}

wait_for_db

if [ "$1" = "run-server" ]; then
    manage_setup
    echo "[Docker] Démarrage du serveur Django sur le port $EXPOSITION_PORT..."
    exec python manage.py runserver 0.0.0.0:"$EXPOSITION_PORT"

elif [ "$1" = "shell-mode" ]; then
    echo "[Docker] Mode Shell interactif."
    exec /bin/bash

else
    exec "$@"
fi