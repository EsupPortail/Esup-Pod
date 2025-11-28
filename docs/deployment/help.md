# Utilities & Maintenance

This document provides helper commands and troubleshooting tips for maintaining the application in both local and production environments.

## Docker Management

### Stopping vs. Removing (CRITICAL)

**Stop Containers:** Stops the running services but preserves containers and internal networks.

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ docker-compose stop
```

**Down (Remove Containers):** Stops and removes containers and networks. Data in volumes is PRESERVED.

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ docker-compose down
```

**Down + Volumes (DESTRUCTIVE):** Stops containers and DELETES database volumes.

⚠️ Warning: Only use this if you want to completely wipe the database and start fresh.

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ docker-compose down -v
```

### Cleaning Up Docker Resources

If you are running out of disk space:

```bash
# Remove unused containers, networks, and dangling images
docker system prune -f
```

## Useful Commands

### Accessing the Shell

To run Python commands or inspect the container environment:

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose exec api bash
root@62d310619d28:/# python manage.py shell
# OR
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose exec api python manage.py shell
```

To inspect db container environment 

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose exec db bash

root@62d310619d28:/# mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"
```

### Makefile Shortcuts

The project includes a Makefile to simplify long Docker commands. Usage examples:

```bash
# Start development server
make up

# build images
make build

# Enter shell
make shell

# View logs
make logs
```

(Check the Makefile in the root directory for the specific command definitions).

## Troubleshooting

### "Static files not found" (404 on CSS/JS)

```bash
sudo docker-compose -f deployment/prod/docker-compose.yml exec backend python manage.py collectstatic --noinput
```

### Database Connection Refused

* Ensure the database container is running: `docker ps`.
* Check if the `DATABASE_URL` in `.env` matches the service name in `docker-compose.yml` (usually `db`).

### Port Conflicts

If you encounter the error **"Address already in use"**, it means another service is already listening on the same port. This commonly occurs for the API (`8000`) or the database (`5432` / `3307`) ports.

#### Steps to resolve:

1. **Check which service is using the port:**

```bash
# Linux / Mac
sudo lsof -i :8000
sudo lsof -i :3307

# Or use netstat
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 3307
```

2. **Stop the conflicting service** or **change the port mapping** in your `docker-compose.yml` file.

For example, to change the development API port:

```yaml
services:
  api:
    ports:
      - "8001:8000"  # Map container port 8000 to host port 8001
```

Or for the database:

```yaml
services:
  db:
    ports:
      - "3308:3306"  # Map container port 3306 to host port 3308
```

3. **Update your `.env` file accordingly** if you change port mappings:

```dotenv
EXPOSITION_PORT=8001
MYSQL_PORT=3308
```

> ⚠️ Always make sure the host ports are **unique** and not in use by any other application.

#### Quick Notes

* `EXPOSITION_PORT` controls the port exposed to your host for the API.
* `MYSQL_PORT` controls the host port for MariaDB.
* Docker container ports (`80`, `8000`, `3306`) remain the same internally; only the host mapping changes.
* If you modify the `.env` file, remember to **rebuild and restart the containers**:

```bash
docker-compose -f deployment/dev/docker-compose.yml build
docker-compose -f deployment/dev/docker-compose.yml up -d
```

