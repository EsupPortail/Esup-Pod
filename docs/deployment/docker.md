# 🐳 Docker Guide

## Essential Commands

All commands must be executed from the project root or from the `deployment/dev` folder by adapting the path.

### 🚀 Start Environment (Dev)

```bash
docker-compose -f deployment/dev/docker-compose.yml up -d --build
```
This will build the images and start the containers (Web, DB, etc.) in the background.

### 📜 View Logs

```bash
docker-compose -f deployment/dev/docker-compose.yml logs -f
```
Add the service name at the end to filter (e.g., `... logs -f web`).

### 🐚 Enter a Container

To execute Django commands (manage.py) directly inside the web container:

```bash
docker-compose -f deployment/dev/docker-compose.yml exec web /bin/bash
# Once inside:
python manage.py shell
```

### 🛑 Stop Services

```bash
docker-compose -f deployment/dev/docker-compose.yml down
```

## Production

In production, use the `deployment/prod/docker-compose.yml` file. Ensure you have configured the `.env.prod` file with secure passwords and `DEBUG=False`.
