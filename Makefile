# Load the .env 
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

DOCKER_COMPOSE_FILE=deployment/dev/docker-compose.yml
DOCKER_COMPOSE_CMD=docker-compose -f $(DOCKER_COMPOSE_FILE)
DOCKER_SERVICE_NAME=api

.PHONY: help start logs shell enter build stop clean runserver test check-django-env

help:
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# COMMANDS (Docker Only)
# ==========================================

start: check-django-env ## Start the full project (auto-setup via entrypoint)
	@echo "Starting Docker environment..."
	$(DOCKER_COMPOSE_CMD) up --build -d
	@echo "Server running in background. Use 'make logs' to follow output."

logs: ## Show real-time logs (see automatic migrations)
	$(DOCKER_COMPOSE_CMD) logs -f $(DOCKER_SERVICE_NAME)

shell: ## Launch a temporary container in shell mode (isolated)
	@echo "Opening an isolated shell..."
	$(DOCKER_COMPOSE_CMD) run --rm --service-ports $(DOCKER_SERVICE_NAME) shell-mode

enter: ## Enter an already running container (for debugging)
	@echo "Entering active container..."
	$(DOCKER_COMPOSE_CMD) exec $(DOCKER_SERVICE_NAME) /bin/bash

build: ## Force rebuild of Docker images
	$(DOCKER_COMPOSE_CMD) build

stop: ## Stop the containers
	$(DOCKER_COMPOSE_CMD) stop

clean: ## Stop and remove everything (containers, orphaned networks, volumes)
	$(DOCKER_COMPOSE_CMD) down --remove-orphans --volumes

runserver: ## Start the server when you using shell mode
	@echo "Use 'make shell' to enter the container, then run 'run-server' or 'python manage.py runserver 0.0.0.0:8000'"
	@echo "This command is deprecated in favor of 'make start' or 'make shell'."

test: ## Run tests inside the container
	@echo "Running tests in Docker..."
	$(DOCKER_COMPOSE_CMD) exec -e DJANGO_SETTINGS_MODULE=config.django.test.docker $(DOCKER_SERVICE_NAME) pytest --cov=src --cov-report=term-missing --cov-fail-under=60

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