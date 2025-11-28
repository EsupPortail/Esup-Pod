FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    libpcre3 \
    libpcre3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.base.txt

COPY deployment/prod/requirements.txt /app/requirements.prod.txt

RUN pip install --no-cache-dir -r requirements.base.txt -r requirements.prod.txt

COPY . .

# ENV PROD
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
ENV STATIC_ROOT=/app/static

RUN mkdir -p /app/static /app/media /app/shared

EXPOSE ${EXPOSITION_PORT}

CMD ["uwsgi", "--ini", "uwsgi.ini"]