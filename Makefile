ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Export current user UID/GID for docker compose
export USER_UID ?= $(shell id -u)
export USER_GID ?= $(shell id -g)

# Configurable variables
DOCKER_COMPOSE_FILE ?= deployment/dev/docker-compose.yml
DOCKER_SERVICE_NAME ?= api
STACK_NAME ?= esup-pod-back
DOCKER_COMPOSE_CMD := docker compose -p $(STACK_NAME) -f $(DOCKER_COMPOSE_FILE)
LOG_PREFIX := \033[36m[make]\033[0m


CMD := $(firstword $(MAKECMDGOALS))
DYNAMIC_CMDS := start stop clean logs shell enter
ifneq ($(filter $(CMD),$(DYNAMIC_CMDS)),)
  SERVICE_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(SERVICE_ARGS):;@:)
endif

define info
	@printf "$(LOG_PREFIX) %s\n" "$(1)"
endef

.PHONY: help start restart full-restart logs shell enter build stop clean ci lint test test-cov check-django-env clean-migrations

help: ## List available make commands
	@grep -h -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands

start: check-django-env ## Start the project/service (detached, build if needed). Usage: make start [service]
	$(call info,Starting Docker environment (service(s): $(if $(SERVICE_ARGS),$(SERVICE_ARGS),all))...)
	@mkdir -p media && chmod 775 media
	$(DOCKER_COMPOSE_CMD) up --build -d $(SERVICE_ARGS)
	$(call info,Server running in background — use 'make logs' to follow output.)

restart: ## Restart containers (stop then start)
	$(call info,Restarting stack '$(STACK_NAME)' (stop -> start)...)
	$(MAKE) stop
	$(MAKE) start

full-restart: ## Full reset then start (clean + start)
	$(call info,Performing full restart: clean -> start...)
	$(MAKE) clean
	$(MAKE) start

logs: ## Follow logs. Usage: make logs [service]
	$(call info,Attaching to logs (service(s): $(if $(SERVICE_ARGS),$(SERVICE_ARGS),all))...)
	@$(DOCKER_COMPOSE_CMD) logs -f --tail=100 $(SERVICE_ARGS)

shell: start ## Launch an isolated shell. Usage: make shell [service]
	$(eval TARGET_SVC=$(if $(SERVICE_ARGS),$(SERVICE_ARGS),$(DOCKER_SERVICE_NAME)))
	$(call info,Opening a new ephemeral shell in service '$(TARGET_SVC)'...)
	$(DOCKER_COMPOSE_CMD) run --rm --service-ports $(TARGET_SVC) shell-mode

enter: start ## Enter an already running container. Usage: make enter [service]
	$(eval TARGET_SVC=$(if $(SERVICE_ARGS),$(SERVICE_ARGS),$(DOCKER_SERVICE_NAME)))
	$(call info,Entering running container for service '$(TARGET_SVC)'...)
	$(DOCKER_COMPOSE_CMD) exec $(TARGET_SVC) /bin/bash

db-shell: start ## Enter the database shell
	$(call info,Entering database shell as root...)
	$(DOCKER_COMPOSE_CMD) exec db mariadb -u root -p$(MYSQL_ROOT_PASSWORD)

build: ## Force Docker image rebuild
	$(call info,Building Docker images (stack: $(STACK_NAME))...)
	$(DOCKER_COMPOSE_CMD) build

stop: ## Stop running containers. Usage: make stop [service]
	$(call info,Stopping containers (service(s): $(if $(SERVICE_ARGS),$(SERVICE_ARGS),all))...)
	$(DOCKER_COMPOSE_CMD) stop $(SERVICE_ARGS)
	$(call info,Containers stopped. Use 'make clean' to remove them entirely.)

ci: build lint test-cov test-api-curl clean ## Local CI pipeline: build → lint → test → test-api → clean
	$(call info,CI sequence completed.)

lint: start ## Run linters (black, flake8) inside the API service
	$(call info,Running black (line length = 90)...)
	$(DOCKER_COMPOSE_CMD) run --rm $(DOCKER_SERVICE_NAME) black . -l 90
	$(call info,Running flake8...)
	$(DOCKER_COMPOSE_CMD) run --rm $(DOCKER_SERVICE_NAME) flake8 src --count --show-source --statistics
	$(call info,Running PyDoc audit...)
	python3 scripts/check_pydocs.py

clean: stop ## Full shutdown and cleanup. Usage: make clean [service]
	$(call info,Cleaning (service(s): $(if $(SERVICE_ARGS),$(SERVICE_ARGS),all))...)
	@if [ -z "$(SERVICE_ARGS)" ]; then \
		$(DOCKER_COMPOSE_CMD) run --rm --user root --no-deps --entrypoint "" $(DOCKER_SERVICE_NAME) bash -c " \
			find . -path '*/migrations/*.py' ! -name '__init__.py' -delete && \
			find . -path '*/migrations/*.pyc' -delete && \
			find . -type d -name '__pycache__' -exec rm -rf {} + \
		" || true; \
		$(DOCKER_COMPOSE_CMD) down --remove-orphans --volumes; \
	else \
		$(DOCKER_COMPOSE_CMD) rm -s -v -f $(SERVICE_ARGS); \
	fi

clean-migrations: ## Delete all migration files (except __init__.py) and .pyc files
	$(call info,Deleting migration files and .pyc/cache files via Docker root user...)
	@$(DOCKER_COMPOSE_CMD) run --rm --user root --no-deps --entrypoint "" $(DOCKER_SERVICE_NAME) bash -c " \
		find . -path '*/migrations/*.py' ! -name '__init__.py' -delete && \
		find . -path '*/migrations/*.pyc' -delete && \
		find . -type d -name '__pycache__' -exec rm -rf {} + \
	" || true
	$(call info,Migrations cleaned.)

test: start ## Run tests inside the container (pytest)
	$(call info,Running tests with DJANGO_SETTINGS_MODULE=config.django.test.docker...)
	$(DOCKER_COMPOSE_CMD) exec -T -e DJANGO_SETTINGS_MODULE=config.django.test.docker $(DOCKER_SERVICE_NAME) bash -c "python3 deployment/dev/scripts/wait_for_db.py && pytest"

test-cov: start ## Run tests with coverage report
	$(call info,Running tests with coverage...)
	$(DOCKER_COMPOSE_CMD) exec -T -e DJANGO_SETTINGS_MODULE=config.django.test.docker $(DOCKER_SERVICE_NAME) bash -c "python3 deployment/dev/scripts/wait_for_db.py && pytest --cov=src --cov-report=term-missing --cov-fail-under=70"

test-api-curl: start ## Run curl-based API tests inside the container
	$(call info,Running curl-based API tests...)
	@$(DOCKER_COMPOSE_CMD) exec -T $(DOCKER_SERVICE_NAME) bash -c "for script in /app/scripts/test_*.sh; do if [ \"\$$script\" != \"/app/scripts/test_base.sh\" ]; then echo \"Running \$$script...\"; bash \"\$$script\" || exit 1; fi; done"

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
