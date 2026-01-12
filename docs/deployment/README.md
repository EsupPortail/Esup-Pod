# 📦 Architecture & Deployment

This project is designed to be easily deployed using **Docker**. The architecture strictly separates Development and Production environments.

## Environment Strategy

| Feature | Development | Production |
| :--- | :--- | :--- |
| **Compose File** | `deployment/dev/docker-compose.yml` | `deployment/prod/docker-compose.yml` |
| **Django Settings** | `src.config.settings.dev` | `src.config.settings.prod` |
| **Database** | SQLite (Local) or MariaDB (Container) | Dedicated Database Service |
| **Debug Mode** | `True` | `False` |

## Directory Structure

```
Pod_V5_Back/
├── deployment/          # Docker Configurations
│   ├── dev/             # Dev Environment
│   └── prod/            # Prod Environment
├── src/                 # Source Code
│   └── config/          # Split Settings (dev.py vs prod.py)
```

## Guides

*   ➡️ **[Docker Guide](docker.md)**: Common commands to start and manage containers.
