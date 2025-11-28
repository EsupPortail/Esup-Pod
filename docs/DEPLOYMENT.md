# Project Overview & Architecture

## Introduction

This documentation outlines the architecture, development workflow, and production deployment strategies for the Pod_V5_Back Django API. The project is designed for scalability and maintainability, utilizing Docker for containerization and a split-settings approach for environment management.

## System Architecture

The application is built on a robust stack designed to ensure separation of concerns between the development and production environments.

* **Backend Framework:** Django (5.2.8) Python (3.12+) with Django Rest Framework (DRF 3.15.2).
* **Database:** MySql (Containerized).
* **Web Server (Prod):** Nginx (Reverse Proxy) + uWSGI (Application Server).
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

| Feature        | Development (dev)                 | Production (prod)                             |
| -------------- | --------------------------------- | --------------------------------------------- |
| Docker Compose | deployment/dev/docker-compose.yml | deployment/prod/docker-compose.yml            |
| Settings File  | src.config.settings.dev           | src.config.settings.prod (or base + env vars) |
| Debug Mode     | True (Detailed errors)            | False (Security hardened)                     |
| Web Server     | runserver (Django built-in)       | Nginx + uWSGI                                 |
| Static Files   | Served by Django                  | Served by Nginx                               |

⚠️ **Important:** Make sure to configure the `.env` file before starting the application. When launching in development mode, Django will use `src.config.settings.dev`. [Example `.env` for Development](dev.md#example-env-for-development)

## Getting Started

* For local setup instructions, see **[Development Guide](deployment/dev.md)**.
* For deployment instructions, see **[Production Guide](deployment/prod.md)**.
* For maintenance and troubleshooting, see **[Help](deployment/help.md)**.
