# Windows Development Guide

Welcome! Choose your preferred development setup below.

Note: If you are on Linux or macOS, please refer to the [Linux/macOS Development Guide](dev_unix.md).

## Quick Start Checklist

If you're familiar with Docker and just want to get started:

```bash
git clone <your-forked-repo-url>
cd Pod_V5_Back

make docker-run # Start the full project (auto-setup via entrypoint)
make docker-enter ## Enter an already running container (for debugging)
make docker-stop # Stop the containers
```

Make tools:
```bash
make docker-logs  # Show real-time logs (see automatic migrations)
make docker-shell # Launch a temporary container in shell mode (isolated)
make docker-runserver # Start the server when you using shell mode
make docker-build # Force rebuild of Docker images
make docker-clean: # Stop and remove everything (containers, orphaned networks, volumes)
```

## Scenario 1: Windows WITH Docker (Recommended)

This is the **recommended method**. It isolates the database and all dependencies for a clean, reliable setup.

### 1. Prerequisites

* Install **Docker Desktop**.
* (Optional but recommended) Enable **WSL2**.

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
   Open PowerShell or CMD in the `deployment/dev` folder and run:

   ```powershell
   cd deployment/dev
   docker-compose up --build -d
   ```

   The `entrypoint.sh` script will automatically:

   * Create the database
   * Apply migrations
   * Create a superuser (`admin/admin`)

### 3. Useful Docker Commands

| Action          | Command (run from `deployment/dev`) |
| --------------- | ----------------------------------- |
| View logs       | `docker-compose logs -f api`        |
| Stop containers | `docker-compose stop`               |
| Full reset      | `docker-compose down -v`            |
| Open shell      | `docker-compose exec api bash`      |


## Scenario 2: Windows WITHOUT Docker (Local Installation)

Use this method if Docker cannot be used. **The project will automatically use SQLite as the database.**

### 1. Prerequisites

* **Python 3.12+** installed

### 2. Installation (PowerShell)

```powershell
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r deployment/dev/requirements.txt
```

### 3. Configuration (.env)

Copy the example environment configuration and customize it:
```bash
cp .env.local .env
```

```bash
# --- Security ---
DJANGO_SETTINGS_MODULE=config.django.dev.docker
SECRET_KEY=change-me-in-prod-secret-key
EXPOSITION_PORT=8000

# --- Superuser ---
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin

# --- Versioning ---
VERSION=5.0.0-DEV
```

### 4. Start the Project

Run the following commands manually:

```powershell
# Apply migrations
python manage.py migrate

# Create an admin user (one-time)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The application will be accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## [Go Back](../dev/dev.md)
