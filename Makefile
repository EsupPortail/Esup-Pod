PYTHON=python3
DJANGO_MANAGE=$(PYTHON) manage.py
DOCKER_COMPOSE_FILE=deployment/dev/docker-compose.yml
DOCKER_COMPOSE_CMD=docker compose -f $(DOCKER_COMPOSE_FILE)
DOCKER_SERVICE_NAME=api

.PHONY: help dev-run dev-logs dev-shell dev-enter dev-build dev-stop dev-clean init migrate makemigrations run superuser test clean setup

# ------------------------------------------
# Help command
# ------------------------------------------
help: ## Display this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==========================================
# DOCKER COMMANDS (Recommended)
# ==========================================

dev-run: ## Start the full project (auto-setup via entrypoint)
	@echo "Starting Docker environment..."
	$(DOCKER_COMPOSE_CMD) up --build -d
	@echo "Server running in background. Use 'make dev-logs' to follow output."

dev-logs: ## Show real-time logs (see automatic migrations)
	$(DOCKER_COMPOSE_CMD) logs -f $(DOCKER_SERVICE_NAME)

dev-shell: ## Launch a temporary container in shell mode (isolated)
	@echo "Opening an isolated shell..."
	$(DOCKER_COMPOSE_CMD) run --rm --service-ports $(DOCKER_SERVICE_NAME) shell-mode

dev-enter: ## Enter an already running container (for debugging)
	@echo "Entering active container..."
	$(DOCKER_COMPOSE_CMD) exec $(DOCKER_SERVICE_NAME) /bin/bash

dev-build: ## Force rebuild of Docker images
	$(DOCKER_COMPOSE_CMD) build

dev-stop: ## Stop the containers
	$(DOCKER_COMPOSE_CMD) stop

dev-clean: ## Stop and remove everything (containers, orphaned networks, volumes)
	$(DOCKER_COMPOSE_CMD) down --remove-orphans --volumes

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

test: ## Run tests locally
	$(DJANGO_MANAGE) test

clean: ## Remove pyc files and caches
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +

# Local setup remains manual, Docker setup is automatic
setup: clean makemigrations migrate
	@echo "Setup complete. Database migrations applied."
	@echo "To create a superuser, run: make superuser"