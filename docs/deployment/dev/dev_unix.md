# Linux & macOS Development Guide

Welcome! This guide uses the included **Makefile** to simplify commands.

Note: If you are on Windows, please refer to the [Windows Development Guide](dev_windows.md).

## Quick Start Checklist

If you're familiar with Docker and just want to get started:

```bash
git clone <your-forked-repo-url>
cd Pod_V5_Back

make dev-run # Start the full project (auto-setup via entrypoint)
make dev-enter ## Enter an already running container (for debugging)
make dev-stop # Stop the containers
```

Make tools:
```bash
make dev-logs  # Show real-time logs (see automatic migrations)
make dev-shell # Launch a temporary container in shell mode (isolated)
make dev-build # Force rebuild of Docker images
make dev-clean: # Stop and remove everything (containers, orphaned networks, volumes)
```


## Scenario 1: Linux/Mac WITH Docker (Recommended)

This is the **recommended method**: fast, isolated, and uses Make to control Docker.

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
SECRET_KEY=change-me-in-prod-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
EXPOSITION_PORT=8000

# --- Database ---
MYSQL_DATABASE=pod_db
MYSQL_USER=pod_user
MYSQL_PASSWORD=pod_password
MYSQL_ROOT_PASSWORD=root_password
MYSQL_HOST=db
MYSQL_PORT=3307

# --- Superuser (Development Only) ---
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
make dev-run
```

This will:

* Build the Docker image
* Start the containers (MariaDB + API)
* Run migrations automatically
* Create a superuser with credentials from `.env`

4. **Follow logs:**

```bash
make dev-logs
```

Watch for any errors during migrations or superuser creation. The logs will show when the server is ready.

Access the API at `http://127.0.0.1:8000` once the logs show "Starting development server".

### 3. Useful Commands (Make + Docker)

| Action | Command          | Description                     |
| ------ | ---------------- | ------------------------------- |
| Enter container | `make dev-enter` | Open a bash shell in the running container |
| Stop   | `make dev-stop`  | Pause the containers (data preserved)            |
| Clean  | `make dev-clean` | Remove containers + volumes (⚠️ deletes database)  |
| Rebuild | `make dev-build` | Force rebuild of Docker images |
| Temp shell | `make dev-shell` | Launch isolated temporary container |

### 4. Database Connection Reference

⚠️ **Important note on ports:**

- **Inside Docker containers:** MariaDB listens on `3306` (use `MYSQL_HOST=db` and `MYSQL_PORT=3306` when connecting from app container)
- **From your machine (host):** MariaDB is exposed on port `3307` (use `localhost:3307` if you connect with a client)
- This mapping is defined in `docker-compose.yml`: `"${MYSQL_PORT:-3307}:3306"`

Example: connecting with MySQL client from your machine:
```bash
mysql -h 127.0.0.1 -P 3307 -u pod_user -p pod_db
```

---

## Scenario 2: Linux/Mac Local

Traditional method. The Makefile helps manage the virtual environment.

### 1. Prerequisites

* Python 3.12+ installe
* venv module (usually included with Python)

Note: You do not need to install a MySQL/MariaDB server locally. The application will automatically switch to SQLite if MySQL configuration is missing.

### 2. Configuration (.env)

Copy the example environment configuration and customize it:
```bash
cp .env.local .env
```

```bash
# --- Security ---
SECRET_KEY=change-me-in-prod-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost
EXPOSITION_PORT=8000

# --- Superuser (Development Only) ---
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin

# --- Versioning ---
VERSION=5.0.0-DEV
```

3. Installation & Starting
The Makefile provides commands for local (non-Docker) usage.

**First-time setup:**
```bash
# Create a virtual environment using workon (mkvirtualenv)
mkvirtualenv pod_v5_back
workon pod_v5_back

# Install dependencies
make init

# Generate migrations and apply them
make makemigrations
make migrate

# Create a superuser interactively
make superuser

# Run the serveur
make run
```

This runs `python manage.py runserver` on port 8000. Access at `http://127.0.0.1:8000`.

### 4. Other Local Commands

| Action     | Command               | Description                    |
| ---------- | --------------------- | ------------------------------ |
| Run tests  | `make test`           | Execute automated tests        |
| Migrations | `make makemigrations` | Generate migration files       |
| Database   | `make migrate`        | Apply pending migrations       |
| Clean      | `make clean`          | Remove `.pyc` files and caches |


## [Go Back](../dev/dev.md)


