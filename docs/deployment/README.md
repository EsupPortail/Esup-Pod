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

```python

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

## Getting Started

- ➡️ **[Development Environment](dev/dev.md)**: Local setup instructions and Docker workflow.

- ➡️ **[Production Deployment](prod/prod.md)**: Production setup and deployment strategies (WIP).

- ⬅️ **[Back to Index](../README.md)**
