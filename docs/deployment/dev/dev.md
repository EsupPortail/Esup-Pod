# Development Environment & Workflow

## Introduction

This guide describes how to set up the development environment for contributing to **Esup-Pod V5**.
We use **Docker** to replicate production services while providing a flexible debugging setup, managed via a **Makefile** for convenience.

## 1. Prerequisites (Choose your OS)

### 🐧 Linux & macOS
*   **Docker** & **Docker Compose** installed.
*   **Make** installed (`sudo apt install make` on Linux or XCode Command Line Tools on macOS).

### 🪟 Windows
*   Install **Docker Desktop**.
*   (Recommended) Enable **WSL2** backend for Docker.
*   Install **Make** (via Git Bash, or `choco install make`).
*   **Note**: Run commands from PowerShell or Git Bash.

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

*   `MYSQL_PASSWORD`, `SECRET_KEY`: Change these for security.
*   `DJANGO_SUPERUSER_PASSWORD`: Default admin password.
*   **Feature Flags**: Toggle authentication methods as needed:
    ```bash
    # --- Authentication Features ---
    USE_LOCAL_AUTH=True
    USE_CAS=False
    USE_LDAP=False
    USE_OIDC=False
    ```

### Managing the App (Make Commands)

We provide a `Makefile` to simplify Docker commands.

| Command | Description |
| :--- | :--- |
| **`make start`** | **Start the full stack** (Builds images, starts DB+API, runs migrations, creates superuser). |
| **`make stop`** | Stop containers (preserves data). |
| **`make logs`** | View real-time logs from containers. |
| **`make shell`** | Launch an isolated temporary shell for debugging. |
| **`make enter`** | Enter the *running* API container (bash). |
| **`make clean`** | **Destructive**: Removes containers and volumes (database is lost). |
| **`make build`** | Force rebuild of Docker images. |

### Running Tests

Tests are executed **inside the Docker container** against a dedicated ephemeral database (`test_pod_db`).
This ensures your development data (`pod_db`) remains untouched and the environment matches CI.

```bash
make test
```

This command will:
1.  Run `pytest` in the container.
2.  Enable **ALL** authentication providers (CAS, LDAP, etc.) to ensure full coverage.
3.  Report code coverage.

### Database Access

*   **From Host Machine**: Connect to `localhost:3307`
    *   User: `pod_user` / Password: `pod_password` (or as set in `.env`)
    *   Database: `pod_db`
*   **From Docker**: Connect to host `db` port `3306`.
