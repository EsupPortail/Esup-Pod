# Development Environment & Workflow

## Introduction

This guide describes how to set up the development environment for contributing to **Esup-Pod V5**.
We use **Docker** to replicate production services while providing a flexible debugging setup, managed via a **Makefile** for convenience.

## 1. Prerequisites (Choose your OS)

### 🐧 Linux & macOS

- **Docker** & **Docker Compose** installed.
- **Make** installed (`sudo apt install make` on Linux or XCode Command Line Tools on macOS).

### 🪟 Windows

- Install **Docker Desktop**.
- (Recommended) Enable **WSL2** backend for Docker.
- Install **Chocolatey** (required to use `choco`): https://chocolatey.org/install
- Install **Make**:
  ```powershell
  choco install make
  ```
- **Note**: Run commands from PowerShell or Git Bash.

---

## 2. Quick Start

If you are familiar with Docker:

```bash
git clone <your-forked-repo-url>
cd Pod_V5_Back

cp .env.docker .env   # Copy template
make start            # Start project
make logs             # Watch logs
```

The app will be available at `http://localhost:8000`.

---

## 3. Development Guide

### Configuration (.env)

The project uses environment variables for configuration.
Copy the included template and customize it if necessary:

```bash
cp .env.docker .env
```

**Key Variables in `.env`:**

- `MYSQL_PASSWORD`, `SECRET_KEY`: Change these for security.
- `DJANGO_SUPERUSER_PASSWORD`: Default admin password.
- **Feature Flags**: Toggle authentication methods as needed:
  ```bash
  # --- Authentication Features ---
  USE_LOCAL_AUTH=True
  USE_CAS=False
  USE_LDAP=False
  USE_OIDC=False
  ```

### Managing the App (Make Commands)

We provide a `Makefile` to simplify Docker commands.

```shell
benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back$ make
help                 List available make commands
start                Start the full project (detached, build if needed)
restart              Restart containers (stop then start)
full-restart         Full reset then start (clean + start)
logs                 Show real-time logs for the main service
shell                Launch an isolated shell in a new container
enter                Enter an already running container
db-shell             Enter the database shell
build                Force Docker image rebuild
stop                 Stop running containers
ci                   Local CI pipeline: build → lint → test → clean
lint                 Run linters (black, flake8) inside the API service
clean                Full shutdown and cleanup (containers, volumes, orphans)
test                 Run tests inside the container (pytest)
test-cov             Run tests with coverage report
check-django-env     Environment checks (DJANGO_SETTINGS_MODULE must end with .docker)
```

### Running Tests

Tests are executed **inside the Docker container** against a dedicated ephemeral database (`test_pod_db`).
This ensures your development data (`pod_db`) remains untouched and the environment matches CI.

```bash
make test
```

### Running CI

You can run the exact same sequence as the CI on your machine to ensure your PR will pass:

```shell
make ci
```

This command chains: build ➔ lint ➔ test-cov ➔ clean.

### Database Access

You can access the database in two ways:

```shell
make db-shell
```
