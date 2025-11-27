FROM python:3.12-slim

WORKDIR /app

# Installation des dépendances système (nécessaires pour mysqlclient et uWSGI)
RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    libpcre3 \
    libpcre3-dev \
    && rm -rf /var/lib/apt/lists/*

# --- GESTION DES DEPENDANCES ---
# 1. Copie du requirements global (racine)
COPY requirements.txt /app/requirements.base.txt
# 2. Copie du requirements de prod (dossier courant deployment/prod)
COPY deployment/prod/requirements.txt /app/requirements.prod.txt

# 3. Installation combinée
RUN pip install --no-cache-dir -r requirements.base.txt -r requirements.prod.txt
# -------------------------------

# Copie du code source
COPY . .

# Configuration de l'environnement
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
ENV STATIC_ROOT=/app/static

# Création des dossiers
RUN mkdir -p /app/static /app/media /app/shared

# NOTE : On a supprimé le 'RUN collectstatic' ici car il est fait au runtime (dans le docker-compose)

EXPOSE 8000

CMD ["uwsgi", "--ini", "uwsgi.ini"]