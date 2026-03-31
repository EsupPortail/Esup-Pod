FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    netcat-openbsd \
    git \
    ffmpeg \
    dos2unix \
    tree \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.base.txt
COPY deployment/dev/requirements.txt /app/requirements.dev.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.base.txt -r requirements.dev.txt

ENV PYTHONPATH=/app:/app/src
ENV DJANGO_SETTINGS_MODULE=config.django.dev.docker

EXPOSE 8000

COPY src /app/src
COPY manage.py /app/manage.py

COPY deployment/dev/scripts/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN dos2unix /usr/local/bin/entrypoint.sh && chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
