FROM python:3.12-slim

WORKDIR /app

# Dépendances système (mysqlclient)
RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Gestion des dépendances
COPY requirements.txt /app/requirements.base.txt
COPY deployment/dev/requirements.txt /app/requirements.dev.txt

RUN pip install --no-cache-dir -r requirements.base.txt -r requirements.dev.txt

# ENV DEV
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=config.settings.dev

EXPOSE 8000

# Mode DEV → on entre dans un bash interactif
CMD ["/bin/bash"]
