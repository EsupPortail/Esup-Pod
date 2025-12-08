# Linux & macOS Development Guide

Welcome! This guide uses the included **Makefile** to simplify commands.

Note: If you are on Windows, please refer to the [Windows Development Guide](dev_windows.md).

## Quick Start Checklist

If you're familiar with Docker and just want to get started:

```bash
git clone <your-forked-repo-url>
cd Pod_V5_Back
cp .env.example .env
make dev-run
make dev-logs  # Follow the startup logs
```

---

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
cp .env.example .env
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

## Scenario 2: Linux/Mac WITHOUT Docker (Local)

Traditional method. The Makefile helps manage the virtual environment.

### 1. Prerequisites

* Python 3.12+ installed
* MySQL development client installed:
  - **Debian/Ubuntu:** `sudo apt install default-libmysqlclient-dev`
  - **macOS (Intel):** See [macOS Intel Setup](#macos-intel-setup) below
  - **macOS (Apple Silicon M1/M2/M3):** See [macOS Apple Silicon Setup](#macos-apple-silicon-setup) below
* Local MySQL/MariaDB server running on `localhost:3306`

### 2. Configuration (.env)

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` to point to your local database. Set `MYSQL_HOST` to `localhost`:

```dotenv
MYSQL_DATABASE=pod_db
MYSQL_USER=pod_user
MYSQL_PASSWORD=pod_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
SECRET_KEY=your-secure-random-key
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your-admin-password
```

### 3. Installation & Starting

The Makefile provides commands for local (non-Docker) usage.

**First-time setup:**

```bash
# Create virtual environment and install dependencies
make init

# Activate the virtual environment (required for the following commands)
source venv/bin/activate

# Generate migrations and apply them
make makemigrations
make migrate

# Create a superuser interactively
make superuser
```

**Daily usage:**

```bash
source venv/bin/activate
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

---

## macOS Setup Specific Instructions

### macOS Intel Setup

If you're setting up on **macOS with Intel processor**, follow these steps to install `mysqlclient`:

**1. Install MySQL client via Homebrew:**

```bash
brew install mysql
```

**2. Set environment variables before installing Python packages:**

```bash
export LDFLAGS="-L$(brew --prefix mysql)/lib"
export CPPFLAGS="-I$(brew --prefix mysql)/include"
```

**3. Install dependencies:**

```bash
make init
```

**4. If you encounter SSL errors, try reinstalling with force flags:**

```bash
source venv/bin/activate
pip install mysqlclient --compile --force-reinstall
```

### macOS Apple Silicon Setup

If you're on **macOS with Apple Silicon (M1, M2, M3, etc.)**, follow these steps:

**1. Install MySQL client via Homebrew:**

```bash
brew install mysql-client
```

⚠️ Note: Use `mysql-client` (not `mysql`) on Apple Silicon for better compatibility.

**2. Add Homebrew MySQL client to your PATH and set environment flags:**

```bash
export PATH="$(brew --prefix mysql-client)/bin:$PATH"
export LDFLAGS="-L$(brew --prefix mysql-client)/lib"
export CPPFLAGS="-I$(brew --prefix mysql-client)/include"
```

**3. Create virtual environment and install:**

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Verify `mysqlclient` installed correctly:**

```bash
python -c "import MySQLdb; print('MySQLdb installed successfully')"
```

**Troubleshooting Apple Silicon:** If installation still fails, consider using conda as an alternative:
```bash
brew install conda
conda create -n pod_env python=3.12
conda activate pod_env
pip install -r requirements.txt
```

---

## Troubleshooting

### Docker container exits immediately

Check logs:
```bash
make dev-logs
```

Common causes:
- `.env` file not created or has wrong paths
- Database connection timeout (wait longer for MariaDB to start)
- Port conflicts (see help.md for resolution)

### mysqlclient installation fails on macOS

Ensure you followed the macOS-specific setup steps above and all environment variables are set before running `make init`.

### Database connection refused

- **With Docker:** Ensure the `db` container is running and healthy: `docker ps`
- **Local:** Ensure MySQL/MariaDB is running: `ps aux | grep -i mysql`
- Verify `.env` has correct `MYSQL_HOST` and `MYSQL_PORT`

---

## [Go Back](../dev/dev.md)


