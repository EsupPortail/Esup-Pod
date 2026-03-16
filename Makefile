ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Configurable variables
DOCKER_COMPOSE_FILE=deployment/dev/docker-compose.yml
DOCKER_SERVICE_NAME=api
STACK_NAME=esup-pod-back
DOCKER_COMPOSE_CMD=docker compose -p $(STACK_NAME) -f $(DOCKER_COMPOSE_FILE)

.PHONY: help start logs shell enter build stop clean test check-django-env

help:
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands
start: check-django-env ## Start the full project
	@echo "Starting Docker environment (stack: $(STACK_NAME))..."
	$(DOCKER_COMPOSE_CMD) up --build -d
	@echo "Server running in background. Use 'make logs' to follow output."

logs: ## Show real-time logs
	$(DOCKER_COMPOSE_CMD) logs -f $(DOCKER_SERVICE_NAME)

shell: ## Launch an isolated shell in a new container
	$(DOCKER_COMPOSE_CMD) run --rm --service-ports $(DOCKER_SERVICE_NAME) shell-mode

enter: ## Enter an already running container
	$(DOCKER_COMPOSE_CMD) exec $(DOCKER_SERVICE_NAME) /bin/bash

build: ## Force rebuild of Docker images
	$(DOCKER_COMPOSE_CMD) build

stop: ## Stop containers
	$(DOCKER_COMPOSE_CMD) stop

clean: ## Stop and remove containers, volumes, networks
	$(DOCKER_COMPOSE_CMD) down --remove-orphans --volumes

test: ## Run tests inside the container
	@echo "Running tests in Docker (stack: $(STACK_NAME))..."
	$(DOCKER_COMPOSE_CMD) exec -e DJANGO_SETTINGS_MODULE=config.django.test.docker $(DOCKER_SERVICE_NAME) pytest --cov=src --cov-report=term-missing --cov-fail-under=60


check-django-env: ## Environment checks
	@if [ "$${DJANGO_SETTINGS_MODULE##*.}" != "docker" ]; then \
		echo "Environment configuration ERROR:"; \
		echo "   To use Docker, configure your .env correctly."; \
		echo "   Current DJANGO_SETTINGS_MODULE: '$${DJANGO_SETTINGS_MODULE}'"; \
		echo "   Expected: must end with '.docker'"; \
		exit 1; \
	fi
