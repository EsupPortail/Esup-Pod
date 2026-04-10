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
- Install **Chocolatey** (required to use `choco`): <https://chocolatey.org/install>
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
cp .env.example .env   # Copy template
make start            # Start project
make logs             # Watch logs
```

The app will be available at `http://localhost:8000`.

## 3. Configuration Guide

Esup-Pod V5 separates **Infrastructure Configuration** (Secrets) from **Feature Flags**.

### Infrastructure & Secrets (`.env`)

The `.env` file is strictly reserved for sensitive information. It should **not** contain boolean flags or UI settings.

- **Contents**: Database passwords, `SECRET_KEY`, API tokens (e.g., `POD_API_TOKEN`), LDAP/OIDC credentials.
- **Setup**: Copy `.env.example` to `.env` and fill in your local credentials.

### Feature Flags (`src/config/settings/`)

Customization is handled via modular Python files instead of a single large environment file.

- **Modular approach**: Each application (e.g., `video`, `authentication`) has its own configuration schema.
- **Customization**: To override default settings, create or modify a Python file in `src/config/settings/{app_name}.py`.
- **Example**: To change the upload limit, edit `src/config/settings/video.py`:

```python
  MAX_UPLOAD_SIZE_GB = 10
```

- **Benefits**: You get full IDE auto-completion and type checking.

### How it works (Pydantic Validation)

The system uses **Pydantic** `BaseSettings` to ensure configuration integrity:

1. **Defaults**: Pydantic loads hardcoded default values.
2. **Secrets**: Sensitive values are injected from the `.env` file.
3. **Overrides**: Specific settings are loaded from `src/config/settings/{app_name}.py`.
4. **Validation**: If a type mismatch occurs (e.g., a string instead of a boolean), the application will fail to start with a clear error message.

### Managing the App (Make Commands)

We provide a `Makefile` to simplify Docker commands.

```shell
user@pod:/usr/local/django_projects/Pod_V5_Back$ make
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

## Further Reading

- ⬅️ **[Back to Deployment Overview](../README.md)**
- ⬅️ **[Back to Index](../../README.md)**
