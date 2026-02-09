ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Configurable variables
DOCKER_COMPOSE_FILE ?= deployment/dev/docker-compose.yml
DOCKER_SERVICE_NAME ?= api
STACK_NAME ?= esup-pod-back
DOCKER_COMPOSE_CMD := docker compose -p $(STACK_NAME) -f $(DOCKER_COMPOSE_FILE)
LOG_PREFIX := \033[36m[make]\033[0m

# Helper: $(call info,Message)
define info
	@printf "$(LOG_PREFIX) %s\n" "$(1)"
endef

.PHONY: help start restart full-restart logs shell enter build stop clean ci lint test test-cov check-django-env

help: ## List available make commands
	@grep -h -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands

start: check-django-env ## Start the full project (detached, build if needed)
	$(call info,Starting Docker environment (stack: $(STACK_NAME))...)
	$(DOCKER_COMPOSE_CMD) up --build -d
	$(call info,Server running in background — use 'make logs' to follow output.)

restart: ## Restart containers (stop then start)
	$(call info,Restarting stack '$(STACK_NAME)' (stop -> start)...)
	$(MAKE) stop
	$(MAKE) start

full-restart: ## Full reset then start (clean + start)
	$(call info,Performing full restart: clean -> start...)
	$(MAKE) clean
	$(MAKE) start

logs: ## Show real-time logs for the main service
	$(call info,Attaching to logs for service '$(DOCKER_SERVICE_NAME)' (tail=100)...)
	$(DOCKER_COMPOSE_CMD) logs -f --tail=100 $(DOCKER_SERVICE_NAME)

shell: start ## Launch an isolated shell in a new container (run --rm)
	$(call info,Opening a new ephemeral shell in service '$(DOCKER_SERVICE_NAME)'...)
	$(DOCKER_COMPOSE_CMD) run --rm --service-ports $(DOCKER_SERVICE_NAME) shell-mode

enter: start ## Enter an already running container (exec)
	$(call info,Entering running container for service '$(DOCKER_SERVICE_NAME)'...)
	$(DOCKER_COMPOSE_CMD) exec $(DOCKER_SERVICE_NAME) /bin/bash

build: ## Force Docker image rebuild
	$(call info,Building Docker images (stack: $(STACK_NAME))...)
	$(DOCKER_COMPOSE_CMD) build

stop: ## Stop running containers
	$(call info,Stopping containers for stack '$(STACK_NAME)'...)
	$(DOCKER_COMPOSE_CMD) stop
	$(call info,Containers stopped. Use 'make clean' to remove them entirely.)

ci: build lint test-cov clean ## Local CI pipeline: build → lint → test → clean
	$(call info,CI sequence completed.)

lint: start ## Run linters (black, flake8) inside the API service
	$(call info,Running black (line length = 90)...)
	$(DOCKER_COMPOSE_CMD) run --rm $(DOCKER_SERVICE_NAME) black . -l 90
	$(call info,Running flake8...)
	$(DOCKER_COMPOSE_CMD) run --rm $(DOCKER_SERVICE_NAME) flake8 src --count --show-source --statistics

clean: stop ## Full shutdown and cleanup (containers, volumes, orphans)
	$(call info,Removing containers, volumes and orphans for stack '$(STACK_NAME)'...)
	$(DOCKER_COMPOSE_CMD) down --remove-orphans --volumes

test: start ## Run tests inside the container (pytest)
	$(call info,Running tests with DJANGO_SETTINGS_MODULE=config.django.test.docker...)
	$(DOCKER_COMPOSE_CMD) exec -T -e DJANGO_SETTINGS_MODULE=config.django.test.docker $(DOCKER_SERVICE_NAME) pytest

test-cov: start ## Run tests with coverage report
	$(call info,Running tests with coverage...)
	$(DOCKER_COMPOSE_CMD) exec -T -e DJANGO_SETTINGS_MODULE=config.django.test.docker $(DOCKER_SERVICE_NAME) pytest --cov=src --cov-report=term-missing --cov-fail-under=60

check-django-env: ## Environment checks (DJANGO_SETTINGS_MODULE must end with .docker)
	$(call info,Checking DJANGO_SETTINGS_MODULE...)
	@if [ -z "$$DJANGO_SETTINGS_MODULE" ]; then \
		printf "$(LOG_PREFIX) %s\n" "ERROR: DJANGO_SETTINGS_MODULE is not set."; \
		exit 1; \
	fi
	@if [ "$${DJANGO_SETTINGS_MODULE##*.}" != "docker" ]; then \
		printf "$(LOG_PREFIX) %s\n" "ERROR: DJANGO_SETTINGS_MODULE must end with '.docker'."; \
		printf "$(LOG_PREFIX) %s\n" "Current value: '$$DJANGO_SETTINGS_MODULE'"; \
		exit 1; \
	fi
	$(call info,Environment OK.)
