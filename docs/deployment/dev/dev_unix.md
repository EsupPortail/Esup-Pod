# Linux & macOS Development Guide

Welcome! This guide uses the included **Makefile** to simplify commands.

Note: If you are on Windows, please refer to the [Windows Development Guide](dev_windows.md).

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


## Development Guide

This is the **supported method**: fast, isolated, and uses Make to control Docker.

### 1. Prerequisites

- Docker & Docker Compose installed  
- Make installed (`sudo apt install make` on Linux or XCode Command Line Tools on macOS)

### 2. Getting Started

1. **Clone and configure:**

```bash
git clone <your-forked-repo-url>
cd Pod_V5_Back
```

2. **Create environment file:**

Copy the example environment configuration and customize it:

```bash
cp .env.docker .env
```

.env.docker file content:
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

# --- Superuser ---
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin

# --- Versioning ---
VERSION=5.0.0-DEV
```

⚠️ **Important:** Edit `.env` to set secure passwords, especially:
- `MYSQL_PASSWORD` (change from default `pod_password`)
- `MYSQL_ROOT_PASSWORD` (change from default `root_password`)
- `SECRET_KEY` (should be a long random string in production)
- `DJANGO_SUPERUSER_PASSWORD` (change from default `admin`)

3. **Start the project:**

```bash
make start
```

This will:

* Build the Docker image
* Start the containers (MariaDB + API)
* Run migrations automatically
* Create a superuser with credentials from `.env`

4. **Follow logs:**

```bash
make logs
```

Watch for any errors during migrations or superuser creation. The logs will show when the server is ready.

Access the API at `http://0.0.0.0:8000` once the logs show "Starting development server".

### 3. Running Tests

Tests are executed **inside the Docker container** against a dedicated MySQL test database (`test_pod_db`).
This ensures that the test environment matches the production environment exactly.

To run tests:

```bash
make test
```

This command will:
1.  Execute `pytest` inside the `api` container.
2.  Use the `config.django.test.docker` settings.
3.  Automatically create/flush the `test_pod_db`.
4.  Run with **all authentication providers enabled** (LDAP, CAS, Shibboleth, OIDC).

> [!NOTE]
> The test database is ephemeral and can be destroyed/recreated by the test runner.
> Do NOT use `test_pod_db` for development data.

### 4. Useful Commands (Make + Docker)

| Action | Command          | Description                     |
| ------ | ---------------- | ------------------------------- |
| Enter container | `make enter` | Open a bash shell in the running container |
| Stop   | `make stop`  | Pause the containers (data preserved)            |
| Clean  | `make clean` | Remove containers + volumes (⚠️ deletes database)  |
| Rebuild | `make build` | Force rebuild of Docker images |
| Temp shell | `make shell` | Launch isolated temporary container |

### 4. Database Connection Reference

⚠️ **Important note on ports:**

- **Inside Docker containers:** MariaDB listens on `3306` (use `MYSQL_HOST=db` and `MYSQL_PORT=3306` when connecting from app container)
- **From your machine (host):** MariaDB is exposed on port `3307` (use `localhost:3307` if you connect with a client)
- This mapping is defined in `docker-compose.yml`: `"${MYSQL_PORT:-3307}:3306"`

Example: connecting with MySQL client from your machine:
```bash
mysql -h 127.0.0.1 -P 3307 -u pod_user -p pod_db
```

## [Go Back](../dev/dev.md)
