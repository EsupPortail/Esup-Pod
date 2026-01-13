# Project Overview & Architecture

## Introduction

This documentation outlines the architecture, development workflow, and production deployment strategies for the Pod_V5_Back Django API. The project is designed for scalability and maintainability, utilizing Docker for containerization and a split-settings approach for environment management.

## System Architecture

The application is built on a robust stack designed to ensure separation of concerns between the development and production environments.

* **Backend Framework:** Django (5.2.8) Python (3.12+) with Django Rest Framework (DRF 3.15.2).
* **Database:** MySql (Containerized).
    * **Local Dev (Lite):** SQLite (Auto-configured if no MySQL config found).
* **Containerization:** Docker & Docker Compose.

## Directory Structure

The project follows a modular structure to separate configuration, source code, and deployment logic:

```
Pod_V5_Back/
├── deployment/          # Docker configurations
│   ├── dev/             # Development specific Docker setup
│   └── prod/            # Production specific Docker setup
├── src/                 # Application Source Code
│   ├── apps/            # Domain-specific Django apps
│   └── config/          # Project configuration (settings, urls, wsgi)
│       └── settings/    # Split settings (base.py, dev.py)
├── docs/                # Documentation
├── manage.py            # Django entry point
├── Makefile             # Command shortcuts
└── requirements.txt     # Python dependencies
```

## Environment Strategy

To ensure stability, the project maintains strict isolation between environments:

| Feature         | Development (Docker)                      | Development (Local)           | Production                                  |
|-----------------|-------------------------------------------|-------------------------------|---------------------------------------------|
| Docker Compose  | deployment/dev/docker-compose.yml         | N/A                           | deployment/prod/docker-compose.yml          |
| Settings File   | src.config.settings.dev                   | src.config.settings.dev       | src.config.settings.prod (ou base + env)    |
| Database        | MariaDB (Service: db)                     | SQLite (db.sqlite3)           | TODO                                        |
| Debug Mode      | True                                      | True                          | TODO                                        |
| Web Server      | runserver                                 | runserver                     | TODO                                        |


### Environment Selection

Make sure to **choose the correct `.env` file** depending on how you run the project:

* **Using Docker → use the Docker `.env.docker` file** (MariaDB, container services)
* **Using local setup → use the local `.env.local` file** (SQLite and local-only defaults)

Selecting the wrong `.env` will load the wrong database configuration and cause the application to fail.



## Getting Started

*   ➡️ **[Development Guide](dev/dev.md)**: Local setup instructions and development environment.
*   ➡️ **[Production Guide (WIP)](../deployment/prod/notes.md)**: Current notes on production deployment.
*   ➡️ **[Help](help.md)**: Maintenance, troubleshooting, and operational support.

*   ⬅️ **[Back to Index](../README.md)**

