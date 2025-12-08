# Development Environment & Workflow

This guide details the setup process for developers contributing to the project. The development environment uses Docker to replicate production dependencies while enabling debugging tools.

## Prerequisites

* Docker Desktop (latest version)
* Git
* Make (Optional, but recommended for shortcut commands)

## Quick Start Checklist

Get started in 5 minutes:

```bash
git clone <your-forked-repo-url>
cd Pod_V5_Back
cp .env.example .env
make dev-run
make dev-logs  # Watch the startup
```

Open `http://127.0.0.1:8000` in your browser once the logs show the server is running.

---

## Initial Setup

### 1. Clone the Forked Repository

Always clone the forked repository and switch to a feature branch. Do not commit directly to main or master.

```bash
git clone <forked_repository_url>
cd Pod_V5_Back
git checkout -b feature/your-feature-name
```

### 2. Environment Configuration

The project relies on environment variables. Create a `.env` file in the root directory.

**Step 1: Copy the example file**

```bash
cp .env.example .env
```

**Step 2: Edit `.env` with your preferred editor** and set secure values:

```dotenv
SECRET_KEY=change-me-to-random-string
ALLOWED_HOSTS=127.0.0.1,localhost
EXPOSITION_PORT=8000

# BDD
MYSQL_DATABASE=pod_db
MYSQL_USER=pod_user
MYSQL_PASSWORD=pod_password
MYSQL_ROOT_PASSWORD=root_password
MYSQL_HOST=db
MYSQL_PORT=3307

# Superuser (Development Only)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=your-secure-password

# Version
VERSION=5.0.0-BETA
```

⚠️ **Security:** Never commit `.env` to Git (already in `.gitignore`).

### 3. Choose Your Operating System Setup

## Windows

**[→ Windows Development Guide](dev_windows.md)**

## Linux / macOS

**[→ Linux & macOS Development Guide](dev_unix.md)**

## [Go Back](../../DEPLOYMENT.md)
