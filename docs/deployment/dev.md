# Development Environment & Workflow

This guide details the setup process for developers contributing to the project. The development environment uses Docker to replicate production dependencies while enabling debugging tools.

## Prerequisites

* Docker Desktop (latest version)
* Git
* Make (Optional, but recommended for shortcut commands)

## Initial Setup

### 1. Clone the Forked Repository

Always clone the forked repository and switch to a feature branch. Do not commit directly to main or master.

```bash
git clone <forked_repository_url>
cd Pod_V5_Back
git checkout -b feature/your-feature-name
```

### 2. Environment Configuration

The project relies on environment variables. Create a `.env` file in the root directory based on the example.

**Example `.env` for Development**

```
SECRET_KEY=secret-key
ALLOWED_HOSTS=127.0.0.1,localhost
EXPOSITION_PORT=8000

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=http://127.0.0.1,http://localhost

# BDD
MYSQL_DATABASE=pod_db
MYSQL_USER=pod_user
MYSQL_PASSWORD=pod_password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307 

# Version
VERSION=5.0.0-BETA
```

### 3. Build and Start Containers

We use the configuration located in `deployment/dev/`.

```bash
# Go to deployment/dev
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back$ cd deployment/dev

# Create symlink to main .env
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$  ln -s ../../.env .env

# Build the images
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose build

# Start the services in the background
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose up -d
```

### 4. Database Initialization

Once the containers are running, apply migrations and create a superuser.

```bash
# Apply migrations
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back$ sudo docker-compose -f deployment/dev/docker-compose.yml exec api make setup

# Create a superuser 
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back$ sudo docker-compose -f deployment/dev/docker-compose.yml exec api make run
```
OR

```bash
# Go to the container terminal
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose exec api bash

# Create a init, migrate, create a super user 
root@62d310619d28:/# make setup

# Start the server
root@62d310619d28:/# make run
```

### 5. Accessing the Application

* **API Root:** [http://localhost:8000/](http://localhost:8000/)
* **Admin Panel:** [http://localhost:8000/admin/](http://localhost:8000/admin/)
* **Swagger Docs:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) 

## Collaborative GitHub Workflow

To maintain code quality and minimize conflicts, adhere to the following workflow:

### Managing Dependencies (`requirements.txt`)

Docker automatically installs the development requirements.

If you install a new package, you must update the requirements file and rebuild.

```bash
# Install locally
pip install <package_name>

# Freeze requirements
pip freeze > deployment/dev/requirements.txt
```

* Commit changes: Include `requirements.txt` in your PR.
* Team update: Other developers must run:

```bash
docker-compose -f deployment/dev/docker-compose.yml build
docker-compose -f deployment/dev/docker-compose.yml up -d
```

### Handling Database Migrations

* Make changes to your `models.py`.
* Generate migration files inside the container:

```bash
docker-compose -f deployment/dev/docker-compose.yml exec backend python manage.py makemigrations
```

* Commit the new migration files located in `src/apps/<app_name>/migrations/`.
* **Conflict Resolution:** If you encounter migration conflicts upon merging, you may need to revert your migration, pull the latest changes, and re-run `makemigrations`.
