# Load the .env 
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

PYTHON=python3
DJANGO_MANAGE=$(PYTHON) manage.py
DOCKER_COMPOSE_FILE=deployment/dev/docker-compose.yml
DOCKER_COMPOSE_CMD=docker compose -f $(DOCKER_COMPOSE_FILE)
DOCKER_SERVICE_NAME=api

.PHONY: help docker-start docker-logs docker-shell docker-enter docker-build docker-stop docker-clean init migrate makemigrations run superuser test clean setup check-django-env

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# DOCKER COMMANDS (Recommended)
# ==========================================

docker-start docker-logs docker-shell docker-enter docker-build docker-stop docker-clean docker-runserver: check-django-env

docker-start: ## Start the full project (auto-setup via entrypoint)
	@echo "Starting Docker environment..."
	$(DOCKER_COMPOSE_CMD) up --build -d
	@echo "Server running in background. Use 'make docker-logs' to follow output."

docker-logs: ## Show real-time logs (see automatic migrations)
	$(DOCKER_COMPOSE_CMD) logs -f $(DOCKER_SERVICE_NAME)

docker-shell: ## Launch a temporary container in shell mode (isolated)
	@echo "Opening an isolated shell..."
	$(DOCKER_COMPOSE_CMD) run --rm --service-ports $(DOCKER_SERVICE_NAME) shell-mode

docker-enter: ## Enter an already running container (for debugging)
	@echo "Entering active container..."
	$(DOCKER_COMPOSE_CMD) exec $(DOCKER_SERVICE_NAME) /bin/bash

docker-build: ## Force rebuild of Docker images
	$(DOCKER_COMPOSE_CMD) build

docker-stop: ## Stop the containers
	$(DOCKER_COMPOSE_CMD) stop

docker-clean: ## Stop and remove everything (containers, orphaned networks, volumes)
	$(DOCKER_COMPOSE_CMD) down --remove-orphans --volumes

docker-runserver: ## Start the server when you using shell mode
	$(DJANGO_MANAGE) runserver 0.0.0.0:${EXPOSITION_PORT}

# ==========================================
# LOCAL COMMANDS (Without Docker)
# ==========================================

init: ## Create local venv and install dependencies
	@echo "Activate venv with 'source venv/bin/activate' then run 'make setup'"
	pip install --upgrade pip
	pip install -r requirements.txt

migrate: ## Apply migrations locally
	$(DJANGO_MANAGE) migrate

makemigrations: ## Generate migration files locally
	$(DJANGO_MANAGE) makemigrations

run: ## Run local Django server
	$(DJANGO_MANAGE) runserver

superuser: ## Create a local superuser
	$(DJANGO_MANAGE) createsuperuser

test: ## Run tests inside Docker (CI environment)
	@echo "Running tests in Docker (CI config)..."
	docker-compose -f deployment/ci/docker-compose.test.yml up -d
	docker-compose -f deployment/ci/docker-compose.test.yml exec -T api pytest --cov=src --cov-report=term-missing --cov-fail-under=70
	docker-compose -f deployment/ci/docker-compose.test.yml down -v

test-native: ## Run tests locally (without Docker)
	$(DJANGO_MANAGE) test --settings=config.django.test.test

clean: ## Remove pyc files and caches
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +


setup: clean makemigrations migrate ## Local setup remains manual, Docker setup is automatic
	@echo "Setup complete. Database migrations applied."
	@echo "To create a superuser, run: make superuser"

check-django-env:
	@# Verify the .env configuration for the Docker context
	@if [ "$${DJANGO_SETTINGS_MODULE##*.}" != "docker" ]; then \
		echo "Environment configuration ERROR:"; \
		echo "   To use Docker, you must correctly configure your .env file."; \
		echo "   Please refer to the deployment documentation."; \
		echo "   Current DJANGO_SETTINGS_MODULE: '$${DJANGO_SETTINGS_MODULE}'"; \
		echo "   Expected: must end with '.docker'"; \
		exit 1; \
	fi