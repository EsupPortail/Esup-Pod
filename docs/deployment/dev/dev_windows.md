# Windows Development Guide

Welcome! This guide assumes a Docker-based workflow using **Docker Desktop**.

Note: If you are on Linux or macOS, please refer to the [Linux/macOS Development Guide](dev_unix.md).

## Quick Start Checklist

If you're familiar with Docker and just want to get started:

```bash
git clone <your-forked-repo-url>
cd Pod_V5_Back

make start  # Start the full project (auto-setup via entrypoint)
make enter  ## Enter an already running container (for debugging)
make stop   # Stop the containers
```

Make tools:
```bash
make logs       # Show real-time logs (see automatic migrations)
make shell      # Launch a temporary container in shell mode (isolated)
make runserver  # Start the server when you using shell mode
make build      # Force rebuild of Docker images
make clean      # Stop and remove everything (containers, orphaned networks, volumes)
```

## Development Guide (Docker)

This is the **supported method**. It isolates the database and all dependencies for a clean, reliable setup.

### 1. Prerequisites

* Install **Docker Desktop**.
* (Optional but recommended) Enable **WSL2**.
* Install **Make** (often included in Git Bash or installable via package managers like Chocolatey: `choco install make`).

### 2. Getting Started

1. **Configuration:**
   Create a `.env` file in the root of the project (copy the example below):

   ```powershell
   cp .env.docker .env
   ```

   `.env.docker` file content:

   ```bash
   # --- Security ---
   DJANGO_SETTINGS_MODULE=config.django.dev.docker
   SECRET_KEY=change-me-in-prod-secret-key
   EXPOSITION_PORT=8000

   # --- Database ---
   MYSQL_DATABASE=pod_db
   MYSQL_USER=pod_user
   MYSQL_PASSWORD=pod_password
   MYSQL_ROOT_PASSWORD=root_password
   MYSQL_HOST=db
   MYSQL_PORT=3307

   # --- Superuser---
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_EMAIL=admin@example.com
   DJANGO_SUPERUSER_PASSWORD=admin

   # --- Versioning ---
   VERSION=5.0.0-DEV
   ```

2. **Start the project:**
   Open PowerShell or CMD in the project root and run:

   ```powershell
   make start
   ```

   The `entrypoint.sh` script will automatically:

   * Create the database
   * Apply migrations
   * Create a superuser (`admin/admin`)

### 3. Running Tests

Tests are executed **inside the Docker container** against a dedicated MySQL test database (`test_pod_db`).

To run tests:

```powershell
make test
```

This ensures:
*   Tests run in the same environment as production.
*   All auth providers are active (`USE_LDAP`, `USE_CAS`, etc).
*   The `test_pod_db` is used, preserving your development data in `pod_db`.

### 4. Useful Docker Commands

| Action          | Command      |
| --------------- | ------------ |
| View logs       | `make logs`  |
| Stop containers | `make stop`  |
| Full reset      | `make clean` |
| Open shell      | `make enter` |

## [Go Back](../dev/dev.md)
