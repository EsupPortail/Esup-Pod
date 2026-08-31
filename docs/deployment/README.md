# Deployment & Architecture: Overview

## Introduction

This documentation outlines the architecture, environment setup, and deployment strategies for Pod V5. The project is designed for scalability and maintainability, utilizing Docker for containerization and a split-settings approach for environment management.

## System Architecture

The application is built on a robust stack designed to ensure separation of concerns between the development and production environments.

- **Backend Framework:** Django with Django Rest Framework (DRF).
- **Database:** MySql (Containerized).
- **Local Dev (Lite):** SQLite (Auto-configured if no MySQL config found).
- **Containerization:** Docker & Docker Compose.

## Directory Structure

The project follows a modular structure to separate configuration, source code, and deployment logic:

```text
Pod_V5_Back/
├── deployment/          # Docker configurations
│   ├── dev/             # Development specific Docker setup
│   └── prod/            # Production specific Docker setup
├── src/                 # Application Source Code
│   ├── apps/            # Domain-specific Django apps
│   └── config/          # Project configuration
│       ├── django/      # Core Project Settings (base, dev, prod)
│       └── settings/    # Functional Customization (features flags: video, auth...)
├── docs/                # Documentation
├── manage.py            # Django entry point
├── Makefile             # Command shortcuts
└── requirements.txt     # Python dependencies
```

## Environment Strategy

To ensure stability, the project maintains strict isolation between environments:

| Feature        | Development (Docker)              | Development (Local)     | Production                               |
| -------------- | --------------------------------- | ----------------------- | ---------------------------------------- |
| Docker Compose | deployment/dev/docker-compose.yml | N/A                     | deployment/prod/docker-compose.yml       |
| Settings File  | src.config.settings.dev           | src.config.settings.dev | src.config.settings.prod (ou base + env) |
| Database       | MariaDB (Service: db)             | SQLite (db.sqlite3)     | TODO                                     |
| Debug Mode     | True                              | True                    | TODO                                     |
| Web Server     | runserver                         | runserver               | TODO                                     |

### Environment Selection

Make sure to **choose the correct `.env` file** depending on how you run the project:

- **Using Docker → use the Docker `.env.example` file** (MariaDB, container services)
- **Using local setup (SQLite and local-only defaults)**

Selecting the wrong `.env` will load the wrong database configuration and cause the application to fail.

---

## Redis Architecture

Redis is a **central component** of Pod V5. It powers four independent functions, each isolated in its own database:

```text
Redis Instance (single node, dev)
 ├── DB 0 ── Celery Broker & Results  (CELERY_BROKER_URL / CELERY_RESULT_BACKEND)
 │            (Background tasks: Esup-Runner task dispatching, batch video deletion, bulk imports)
 ├── DB 1 ── Django Cache             (REDIS_CACHE_URL)
 │            ├── pod:video:metadata      TTL=600s
 │            ├── pod:search:results:*    TTL=60s
 │            └── pod:search:facets:*     TTL=120s
 └── DB 2 ── User Sessions            (REDIS_SESSION_URL)

Redis Search Instance (dedicated, Redis 8)
 └── DB 0 ── Full-text Search Index   (SEARCH_REDIS_URL)
              └── FT.SEARCH / FT.AGGREGATE on pod:video:<id>
```

### Environment Variables

| Variable               | Role                       | Default (dev)                  |
| :--------------------- | :------------------------- | :----------------------------- |
| `CELERY_BROKER_URL`    | Celery task queue broker   | `redis://redis:6379/0`         |
| `CELERY_RESULT_BACKEND`| Celery result storage      | `redis://redis:6379/0`         |
| `REDIS_CACHE_URL`      | Django cache backend       | `redis://redis:6379/1`         |
| `REDIS_SESSION_URL`    | Session backend            | `redis://redis:6379/2`         |
| `REDIS_PASSWORD`       | Auth password (optional)   | *(empty)*                      |
| `SEARCH_REDIS_URL`     | Redis Search connection    | `redis://redis-search:6379/0`  |
| `CACHE_TIMEOUT`        | Default cache TTL (seconds)| `600`                          |

> [!IMPORTANT]
> If `REDIS_CACHE_URL` is **not set**, Django falls back to `LocMemCache` (in-memory, per-process, no sharing between workers). This is fine for local dev but **must not be used in production**.

### Production Recommendation

For production deployments with multiple workers, use **separate Redis instances** to avoid resource contention:

```yaml
# docker-compose.prod.yml (example)
services:
  redis:          # DB 0-2 : Celery, cache, sessions
    image: redis:7-alpine

  redis-search:   # Redis 8 with Search module
    image: redis/redis-stack-server:latest
```

---

## Getting Started

- ➡️ **[Development Environment](dev/dev.md)**: Local setup instructions and Docker workflow.
- ➡️ **[Production Deployment](prod/prod.md)**: Production setup and deployment strategies (WIP).
- ➡️ **[Data Migration (V4 to V5)](migration_v4_to_v5.md)**: Steps and scripts to migrate your existing database and media to V5.
- ⬅️ **[Back to Index](../README.md)**

