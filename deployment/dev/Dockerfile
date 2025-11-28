FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.base.txt
COPY deployment/dev/requirements.txt /app/requirements.dev.txt

RUN pip install --no-cache-dir -r requirements.base.txt -r requirements.dev.txt

# ENV DEV
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=config.settings.dev

EXPOSE ${EXPOSITION_PORT}

CMD ["/bin/bash"]
