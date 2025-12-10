# Help & Troubleshooting Guide

This guide addresses common questions and errors encountered during development setup. **Select your operating system below to jump to the relevant section.**

## Table of Contents

- [General Questions (All Platforms)](#general-questions-all-platforms)
- [Linux & macOS Troubleshooting](#linux--macos-troubleshooting)
- [Windows Troubleshooting](#windows-troubleshooting)
- [Docker Issues (All Platforms)](#docker-issues-all-platforms)
- [Database Issues](#database-issues)
- [Quick Reference](#quick-reference)

---

## General Questions (All Platforms)

### Q: Which setup should I choose?

**Answer:**
- **With Docker (Recommended):** Fastest, cleanest, isolates all dependencies. Works identically across Windows, Mac, and Linux.
- **Without Docker (Local):** Lightweight, good for experienced developers. More setup work, and database varies by OS (SQLite fallback available).

**Recommendation:** Use Docker unless you have a specific reason not to.

---

### Q: What's the difference between `.env.docker` and `.env.local`?

**Answer:**
- `.env.docker` → Use when running with Docker (has MySQL/MariaDB credentials)
- `.env.local` → Use for local setup without Docker (SQLite database)
- **Important:** Copy the correct file to `.env` or the app will load wrong database settings!

```bash
# If using Docker:
cp .env.docker .env

# If using local setup:
cp .env.local .env
```

---

### What do the environment variables mean?

| Variable | Purpose | Example |
|----------|---------|---------|
| `SECRET_KEY` | Django security key (must be random in production) | `django-insecure-abc...` |
| `EXPOSITION_PORT` | The port the app runs on | `8000` |
| `MYSQL_HOST` | Database server address (Docker: `db`, Local: `localhost`) | `db` (Docker) or `localhost` (Local) |
| `MYSQL_PORT` | Database server port | `3306` (Docker internal) or `3307` (Local) |
| `DJANGO_SUPERUSER_*` | Admin account credentials (dev only) | `admin` |

---

### How do I reset everything and start fresh?

**Docker:**
```bash
make dev-clean  # Delete containers, networks, volumes (⚠️ database erased)
make dev-run    # Start fresh
```

**Local (without Docker):**
```bash
rm src/db.sqlite3       # Delete SQLite database
make clean              # Remove cache files
make makemigrations     # Recreate migrations
make migrate            # Apply to fresh database
make superuser          # Create new admin user
make run
```

---

### Can I switch between Docker and local setup?

**Answer:** Yes, but you need to:

1. Stop the current setup
2. Copy the correct `.env` file
3. Start the new setup

```bash
# Switching FROM Docker TO Local
make dev-clean
cp .env.local .env
make migrate
make run
```

---

### The server starts but shows errors. How do I debug?

**Docker:**
```bash
make dev-logs  # Show real-time logs with all errors
```

**Local:**
```bash
make run  # Logs appear in the terminal
```

Look for error messages. **Common issues are in the [specific troubleshooting sections below](#linux--macos-troubleshooting).**

---

## Linux & macOS Troubleshooting

### Error: `command not found: make`

**Cause:** Make is not installed.

**Solution:**

**macOS:**
```bash
# Install XCode Command Line Tools
xcode-select --install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install make
```

---

### Error: `command not found: docker`

**Cause:** Docker is not installed or not in PATH.

**Solution:**

**macOS:**
- Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- Launch Docker Desktop and verify it runs in the background

**Linux:**
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER  # Add your user to docker group (restart shell after)
```

---

### Error: `docker-compose: command not found` or `compose is not available`

**Cause:** Docker Compose is not installed or outdated Docker version.

**Solution:**

```bash
# Check version
docker-compose --version  # Should be 1.29+

# If not installed or outdated
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

Alternatively, use the newer `docker compose` (without hyphen):
```bash
make dev-run  # Will use docker-compose internally
```

---

### Error: `Permission denied while trying to connect to Docker daemon`

**Cause:** Your user doesn't have permission to use Docker.

**Solution:**
```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Apply group changes (one of these):
newgrp docker        # Activate immediately in current shell
# OR restart your terminal/computer

# Verify it works
docker ps  # Should list containers (even if empty)
```

---

### Error: `mkvirtualenv: command not found` (Local setup)

**Cause:** `virtualenvwrapper` is not installed (optional tool for convenience).

**Solution:** Use Python's built-in venv instead:

```bash
python3 -m venv venv
source venv/bin/activate
make init
```

If you want `mkvirtualenv`:
```bash
pip install virtualenvwrapper
# Add to ~/.bashrc or ~/.zshrc:
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
```

---

### Error: `ModuleNotFoundError: No module named 'django'` (Local setup)

**Cause:** Virtual environment is not activated or dependencies not installed.

**Solution:**
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Check if activated (should show (venv) in prompt)

# 3. Install dependencies
make init

# 4. Try running again
make run
```

---

### Error: `django.db.utils.OperationalError: no such table: auth_user`

**Cause:** Database migrations haven't been run.

**Solution:**
```bash
# Activate venv first (local setup)
source venv/bin/activate

# Run migrations
make migrate

# Try again
make run
```

---

### Error: `Address already in use` or `Port 8000 is already in use`

**Cause:** Another process is using port 8000.

**Solution:**

Find and stop the process:
```bash
# Find process using port 8000
lsof -i :8000
# Or with netstat
netstat -tulpn | grep 8000

# Kill the process (replace PID with the actual ID)
kill -9 <PID>
```

Or use a different port:
```bash
make run 8001  # Run on port 8001 instead
# Or manually:
python3 manage.py runserver 8001
```

---

### Error: `OSError: [Errno 48] Address already in use` (Docker)

**Cause:** Port 8000 or 3307 is already in use by another service.

**Solution:**

**Option 1:** Stop the other service/container:
```bash
make dev-stop
docker ps  # Check if any containers are still running
docker kill <container_id>  # Stop them if needed
```

**Option 2:** Use different ports by editing `.env`:
```bash
EXPOSITION_PORT=8001      # Change from 8000 to 8001
MYSQL_PORT=3308           # Change from 3307 to 3308
```

Then restart:
```bash
make dev-clean
make dev-run
```

---

### Error: `Error response from daemon: insufficient memory`

**Cause:** Docker containers need more memory.

**Solution:**

Open Docker Desktop → Preferences → Resources → Memory, increase to 4GB+ (or more if available).

---

### Error: `sudo: make: command not found`

**Cause:** Running with `sudo` prevents finding locally installed tools.

**Solution:** Never use `sudo` with make/docker commands:

```bash
# ❌ Wrong:
sudo make dev-run

# ✅ Correct:
make dev-run
```

If you get permission denied errors, add your user to the docker group (see [Permission denied while trying to connect to Docker daemon](#error-permission-denied-while-trying-to-connect-to-docker-daemon) above).

---

## Windows Troubleshooting

### Error: `docker` is not recognized

**Cause:** Docker Desktop is not installed or not in PATH.

**Solution:**

1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Enable **WSL2** during installation (recommended)
3. Restart PowerShell/CMD and try again

```powershell
docker --version  # Should show Docker version
```

---

### Error: `make` is not recognized

**Cause:** GNU Make is not installed on Windows.

**Solution (Choose ONE):**

**Option A: Use Docker (easiest)**
Just run docker commands directly (you don't need `make`):
```powershell
cd deployment/dev
docker-compose up --build -d
docker-compose logs -f api
docker-compose stop
```

**Option B: Install Make via Chocolatey**
```powershell
# Install Chocolatey first if you don't have it
# https://chocolatey.org/install

choco install make
```

**Option C: Install via Git Bash**
If you have Git for Windows installed, use Git Bash instead of PowerShell:
```bash
make dev-run
```

**Option D: Install via WSL2**
```powershell
wsl --install  # Install WSL2
# Inside WSL:
sudo apt install make
make dev-run
```

---

### Error: `docker-compose: command not found` (or similar)

**Cause:** Docker Compose is not installed or outdated.

**Solution:**

```powershell
# Check version (should be 1.29+)
docker-compose --version

# Update Docker Desktop to latest version
# https://www.docker.com/products/docker-desktop
```

Or use newer `docker compose` syntax (without hyphen):
```powershell
docker compose up --build -d
docker compose logs -f api
```

---

### Error: `The term '.\venv\Scripts\Activate.ps1' is not recognized` (Local setup)

**Cause:** PowerShell execution policy blocks scripts, or venv doesn't exist.

**Solution:**

**Option 1: Create venv first**
```powershell
python -m venv venv  # Create virtual environment
.\venv\Scripts\Activate.ps1
```

**Option 2: Fix execution policy (if venv exists)**
```powershell
# Run this once in PowerShell (as Administrator):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate:
.\venv\Scripts\Activate.ps1
```

**Option 3: Use cmd.exe instead of PowerShell**
```cmd
venv\Scripts\activate.bat
```

---

### Error: `python: command not found` or `'python' is not recognized`

**Cause:** Python is not installed or not in PATH.

**Solution:**

1. Install [Python 3.12+](https://www.python.org/downloads/)
2. **During installation, check "Add Python to PATH"**
3. Restart PowerShell/CMD

```powershell
python --version  # Should show Python 3.12+
```

If already installed but not in PATH:
- Go to Control Panel → Environment Variables
- Add Python installation folder to PATH
- Restart PowerShell

---

### Error: `pip: command not found` (Local setup)

**Cause:** pip is not installed or virtual environment not activated.

**Solution:**

```powershell
# Activate venv first:
.\venv\Scripts\Activate.ps1

# Then try pip:
pip --version

# If still not found, upgrade Python's venv module:
python -m pip install --upgrade pip
```

---

### Error: `ModuleNotFoundError: No module named 'django'` (Local setup)

**Cause:** Virtual environment is not activated or dependencies not installed.

**Solution:**

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Check (should show (venv) in prompt)

# 3. Install dependencies
pip install -r requirements.txt
pip install -r deployment/dev/requirements.txt

# 4. Try running again
python manage.py runserver
```

---

### Error: `Port 8000 is already in use` (Local setup)

**Cause:** Another process is using port 8000.

**Solution:**

Find and stop the process:
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use different port:
python manage.py runserver 8001
```

---

### Error: `docker-compose up` fails with MySQL/MariaDB errors

**Cause:** Port 3307 is in use or database service didn't start.

**Solution:**

```powershell
# Check if service is running
docker-compose ps

# View detailed logs
docker-compose logs db   # Database logs
docker-compose logs api  # App logs

# Hard reset
docker-compose down -v
docker-compose up --build -d
docker-compose logs -f   # Watch startup
```

---

### Error: `.env` file not found or not being read

**Cause:** `.env` file doesn't exist or is in wrong location.

**Solution:**

```powershell
# Ensure you're in the project root (Pod_V5_Back folder)
cd Pod_V5_Back

# Copy .env template
cp .env.docker .env

# Edit it with your settings
notepad .env  # or use your editor
```

The `.env` file **must be in the project root**, not in `deployment/dev/`.

---

### Error: `WSL2 not found` or `Docker can't connect to Linux kernel`

**Cause:** WSL2 is not installed or not set as default.

**Solution:**

```powershell
# Run as Administrator:
wsl --install

# Set WSL2 as default:
wsl --set-default-version 2

# Restart Docker Desktop

# Verify:
docker run hello-world
```

---

## Docker Issues (All Platforms)

### Error: `docker: ERROR: Couldn't connect to Docker daemon`

**Cause:** Docker daemon is not running.

**Solution:**

**macOS/Windows:**
- Open Docker Desktop and wait for it to fully start

**Linux:**
```bash
sudo systemctl start docker
sudo systemctl enable docker  # Auto-start on boot
```

---

### Error: `ERROR: service "api" not found` or `No such service`

**Cause:** Docker Compose configuration is incorrect or service is not defined.

**Solution:**

```bash
# Check if docker-compose.yml exists and is valid
cat deployment/dev/docker-compose.yml

# Rebuild and try again
make dev-clean
make dev-build
make dev-run
```

---

### Error: `ERROR: "db" image not found`

**Cause:** MariaDB image hasn't been pulled or internet connection issue.

**Solution:**

```bash
# Pull images manually
docker pull mariadb:latest

# Try again
make dev-run
```

If it still fails, check internet connection and try:
```bash
make dev-build --no-cache
```

---

### Error: `Binding to port 8000 failed: Address already in use`

**Cause:** Another container or service is using port 8000.

**Solution:**

```bash
# Stop all containers
make dev-stop
docker stop $(docker ps -q)  # Stop all running containers

# Check what's using the port:
# macOS/Linux:
lsof -i :8000

# Windows PowerShell:
netstat -ano | findstr :8000

# Remove the blocking service or use different port (edit .env)
```

---

### Error: `docker-compose: 'logs' is not a docker-compose command`

**Cause:** Outdated Docker Compose version.

**Solution:**

```bash
# Update Docker Desktop or manually update Compose
# https://docs.docker.com/compose/install/

# Or use new syntax:
docker compose logs -f api  # No hyphen
```

---

### Error: `ERROR: yaml.scanner.ScannerError` in docker-compose.yml

**Cause:** YAML syntax error in docker-compose.yml file.

**Solution:**

```bash
# Check the file for formatting issues
cat deployment/dev/docker-compose.yml

# Common issues:
# - Incorrect indentation (use spaces, not tabs)
# - Missing colons after keys
# - Quotes around values not closed

# Validate YAML online or with a tool
```

---

### Containers start but app doesn't respond

**Cause:** App is still starting or not listening on correct port.

**Solution:**

```bash
# Check logs in real-time
make dev-logs

# Look for "Starting development server" message

# If migrations are still running, wait a moment

# Check if containers are actually running
docker-compose ps

# Try connecting manually
curl http://localhost:8000
```

---

### Database connection fails inside container

**Cause:** `MYSQL_HOST` or `MYSQL_PORT` is incorrect.

**Solution:**

Inside Docker, use:
```bash
# Correct for Docker:
MYSQL_HOST=db        # Service name, not localhost
MYSQL_PORT=3306      # Internal port, not 3307
```

From your machine (host), use:
```bash
MYSQL_HOST=localhost  # or 127.0.0.1
MYSQL_PORT=3307       # Exposed port
```

The `.env` file is for the container, so use the Docker values (db, 3306).

---

## Database Issues

### Error: `django.db.utils.OperationalError: no such table: auth_user`

**Cause:** Database migrations haven't run.

**Solution:**

**Docker:**
```bash
make dev-enter
python manage.py migrate
exit
```

**Local:**
```bash
make migrate
```

---

### Error: `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`

**Cause:** Database service is not running or credentials are wrong.

**Solution:**

**Docker:**
```bash
# Check if database container is running
docker-compose ps

# Check database logs
docker-compose logs db

# If not running, restart
make dev-clean
make dev-run
```

**Local:**
```bash
# Verify MySQL/MariaDB is running
sudo systemctl status mysql
# or
mysql -u root -p  # Try connecting manually

# If not installed, install:
# Ubuntu: sudo apt install mysql-server
# macOS: brew install mysql
```

Also verify `.env` has correct credentials.

---

### Error: `django.db.utils.OperationalError: (1045, "Access denied for user 'pod_user'@'db')")`

**Cause:** Database credentials are wrong in `.env`.

**Solution:**

```bash
# 1. Check .env file
cat .env

# 2. Verify credentials match docker-compose.yml
cat deployment/dev/docker-compose.yml

# 3. If wrong, delete and recreate
make dev-clean

# 4. Edit .env with correct credentials
# Make sure MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST match

# 5. Restart
make dev-run
```

---

### Migrations not applying automatically

**Cause:** Migrations folder or migration files missing.

**Solution:**

**Docker:**
```bash
make dev-enter
python manage.py makemigrations
python manage.py migrate
exit
```

**Local:**
```bash
make makemigrations
make migrate
```

---

## Quick Reference

### Docker Commands (Make shortcuts - Linux/macOS)

| Task | Command | Notes |
|------|---------|-------|
| Start | `make dev-run` | Builds + starts containers |
| Logs | `make dev-logs` | View real-time logs |
| Enter | `make dev-enter` | Open shell in running container |
| Stop | `make dev-stop` | Pause containers (data preserved) |
| Clean | `make dev-clean` | Delete everything (⚠️ data lost) |
| Rebuild | `make dev-build` | Force rebuild images |

### Docker Commands (Direct - All platforms)

| Task | Command |
|------|---------|
| Start | `docker-compose -f deployment/dev/docker-compose.yml up --build -d` |
| Logs | `docker-compose -f deployment/dev/docker-compose.yml logs -f api` |
| Stop | `docker-compose -f deployment/dev/docker-compose.yml stop` |
| Enter | `docker-compose -f deployment/dev/docker-compose.yml exec api bash` |

### Local Commands (Make shortcuts - Linux/macOS)

| Task | Command |
|------|---------|
| Setup | `make init` |
| Migrate | `make migrate` |
| Run | `make run` |
| Create Admin | `make superuser` |
| Tests | `make test` |
| Clean cache | `make clean` |

### Important Ports & Hosts

| Service | Docker Internal | Exposed (Host) | Purpose |
|---------|-----------------|----------------|---------|
| Django App | 8000 | 8000 (`.env`: `EXPOSITION_PORT`) | Web API |
| MariaDB | 3306 | 3307 (`.env`: `MYSQL_PORT`) | Database |

### Environment Variables Checklist

- [ ] `.env` file created (copied from `.env.docker` or `.env.local`)
- [ ] `SECRET_KEY` is set
- [ ] `ALLOWED_HOSTS` includes your dev address
- [ ] `MYSQL_HOST` = `db` (Docker) or blank/localhost (Local)
- [ ] `MYSQL_PORT` = `3306` (Docker) or blank (Local SQLite)
- [ ] `DJANGO_SUPERUSER_PASSWORD` is changed from `admin`

---

## Still Stuck?

If none of these solutions work:

1. **Run diagnostics:**
   ```bash
   # Docker status
   docker --version
   docker-compose --version
   docker ps -a
   
   # Python version (local setup)
   python --version
   pip --version
   
   # .env file check
   cat .env
   ```

2. **Check logs carefully** - the first error is usually the real issue:
   ```bash
   make dev-logs  # Docker
   # or
   make run       # Local
   ```

3. **Reset everything and try again:**
   ```bash
   make dev-clean
   make dev-run
   make dev-logs
   ```

4. **Check the deployment guides:**
   - [Linux/macOS Development Guide](dev_unix.md)
   - [Windows Development Guide](dev_windows.md)
   - [Main Deployment Guide](../DEPLOYMENT.md)

---

## [Go Back to Main Deployment Guide](../DEPLOYMENT.md)

