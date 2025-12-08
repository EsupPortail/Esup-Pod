# 🚀 CONTRIBUTING.md - Pod_V5_Back

Welcome to the Pod_V5_Back project! This guide will help you set up your development environment and start contributing.

## Quick Start (5 minutes)

If you're familiar with Docker, this is all you need:

```bash
# 1. Clone the repository
git clone https://github.com/<YOUR-USERNAME>/Pod_V5_Back.git
cd Pod_V5_Back

# 2. Create configuration file
cp .env.example .env

# 3. Start development environment
make dev-run

# 4. Watch the startup logs
make dev-logs

# 5. Access the application
# Open http://127.0.0.1:8000 in your browser
```

---

## System Requirements

### Docker Setup (Recommended)

- Docker Desktop (latest version)
- Docker Compose (included with Docker Desktop)
- Make (macOS: XCode Command Line Tools, Linux: `sudo apt install make`)
- 2-4 GB RAM available for Docker

### Local Setup (Advanced)

- Python 3.12+
- MySQL/MariaDB 5.7+ or equivalent
- Build tools:
  - **Debian/Ubuntu:** `default-libmysqlclient-dev`, `build-essential`
  - **macOS Intel:** Homebrew with `mysql`
  - **macOS M1/M2+:** Homebrew with `mysql-client`

---

## Detailed Setup Guides

Choose your setup method:

- **[🐳 Docker Setup (Linux/macOS)](docs/deployment/dev/dev_unix.md)** - Recommended
- **[🐧 Local Development (Linux/macOS)](docs/deployment/dev/dev_unix.md#scenario-2-linuxmac-without-docker-local)**
- **[🪟 Windows Setup](docs/deployment/dev/dev_windows.md)**

---

## Project Structure

```
Pod_V5_Back/
├── src/                    # Application source code
│   ├── apps/              # Django apps (authentication, info, utils)
│   └── config/            # Django configuration & settings
├── deployment/            # Docker configurations
│   ├── dev/              # Development Docker setup
│   └── prod/             # Production setup (WIP)
├── docs/                 # Documentation
│   └── deployment/       # Deployment guides
├── Makefile              # Development commands
├── requirements.txt      # Python dependencies
├── manage.py             # Django management script
└── .env.example          # Example environment configuration
```

---

## Development Workflow

### 1. Create a Feature Branch

Always work on a feature branch, never directly on `main` or `develop`:

```bash
git checkout -b feature/your-feature-name
```

### 2. Start the Development Server

```bash
# With Docker (recommended)
make dev-run
make dev-logs  # Watch the output in another terminal

# OR without Docker (if you did local setup)
source venv/bin/activate
make run
```

### 3. Access the Application

- **API:** http://127.0.0.1:8000/api/
- **Admin:** http://127.0.0.1:8000/admin/
- **Superuser:** `admin` / `admin` (from `.env.example`, change for production)

### 4. Make Your Changes

Edit code in your favorite IDE. Changes are automatically reflected when using Docker volumes.

### 5. Test Your Changes

```bash
# Run tests locally
make test

# OR with Docker
make dev-enter  # Enter container
python manage.py test
```

### 6. Check Database State

```bash
# Enter the application container
make dev-enter

# Or just the database
make dev-enter  # then:
# mysql -h db -u pod_user -p pod_db

# Run Django shell
python manage.py shell
```

### 7. Commit and Push

```bash
git add .
git commit -m "Clear description of your changes"
git push origin feature/your-feature-name
```

### 8. Create a Pull Request

Push your branch and create a PR on GitHub. Fill in the PR template and wait for review.

---

## Useful Commands

### Docker Commands

```bash
make dev-run          # Start all containers
make dev-stop         # Stop containers (data preserved)
make dev-clean        # Remove containers & volumes (caution: deletes data)
make dev-logs         # Show live logs
make dev-enter        # Enter running container shell
make dev-shell        # Launch isolated temporary container
make dev-build        # Force rebuild of images
```

### Django Commands (in container or local)

```bash
python manage.py migrate              # Apply migrations
python manage.py makemigrations       # Create new migrations
python manage.py createsuperuser      # Create admin user
python manage.py test                 # Run tests
python manage.py shell                # Interactive Python shell
python manage.py collectstatic        # Collect static files
```

### Makefile Local Commands

```bash
make init             # Create virtual environment
make run              # Run development server locally
make migrate          # Apply migrations locally
make makemigrations   # Create migrations locally
make test             # Run tests locally
make clean            # Clean Python cache files
```

---

## Troubleshooting

### "Address already in use" Error

If you get an error about ports `8000` or `3307` already being in use:

```bash
# Find what's using the port (Linux/macOS)
sudo lsof -i :8000
sudo lsof -i :3307

# Either stop the conflicting process or change the port in .env
# Example: EXPOSITION_PORT=8001
```

### Docker Doesn't Start

Check the logs:

```bash
make dev-logs
```

Common issues:
- `.env` file not created → Run `cp .env.example .env`
- Port conflict → Check `EXPOSITION_PORT` and `MYSQL_PORT` in `.env`
- Database not ready → Wait a few seconds, logs will show when ready
- Disk space → Run `docker system prune -f` to clean unused images

### Database Connection Error

If you get "Connection refused" or similar:

**With Docker:**
```bash
# Check if database container is running
docker ps

# Check database health
docker logs pod_mariadb_dev
```

**Locally:**
```bash
# Ensure MySQL is running
ps aux | grep -i mysql

# Test connection
mysql -h localhost -u pod_user -p pod_db
```

### macOS: mysqlclient Installation Fails

If `pip install mysqlclient` fails on macOS:

```bash
# For Intel Mac
brew install mysql
export LDFLAGS="-L$(brew --prefix mysql)/lib"
export CPPFLAGS="-I$(brew --prefix mysql)/include"
make init

# For Apple Silicon (M1/M2+)
brew install mysql-client
export PATH="$(brew --prefix mysql-client)/bin:$PATH"
export LDFLAGS="-L$(brew --prefix mysql-client)/lib"
export CPPFLAGS="-I$(brew --prefix mysql-client)/include"
make init
```

---

## Code Guidelines

### Python/Django

- Follow PEP 8 style guide
- Use type hints where possible
- Add docstrings to functions and classes
- Keep functions small and focused

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add user authentication endpoint
fix: correct database migration order
docs: update deployment guide
refactor: simplify superuser creation logic
test: add tests for API authentication
```

### Pull Requests

- Keep PRs focused on a single feature or fix
- Include description of what and why
- Reference related issues with `#123`
- Ensure all tests pass before submitting

---

## Documentation

- **[Project Overview](../DEPLOYMENT.md)** - System architecture
- **[Development Setup](dev/dev.md)** - Platform-specific setup
- **[Help & Troubleshooting](help.md)** - Common issues
- **[Deployment Guide](prod.md)** - Production deployment (coming soon)

---

## Getting Help

- 💬 Check existing issues and discussions
- 📖 Read the [Help documentation](help.md)
- 🐛 Create a new issue if you find a bug
- ❓ Ask questions in issues with clear examples

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please read our [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md) before contributing.

---

## Security

If you discover a security vulnerability, please email [security contact] instead of using the issue tracker. See [SECURITY.md](../../SECURITY.md) for more details.

---

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Git Documentation](https://git-scm.com/doc)

---

**Happy coding! 🎉**

If you have questions or suggestions for improving this guide, please let us know!
