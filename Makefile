
PYTHON=python3
DJANGO_MANAGE=$(PYTHON) manage.py

DOCKER_COMPOSE_FILE=deployment/dev/docker-compose.yml
# Utilisation de la syntaxe moderne v2 'docker compose' au lieu de 'docker-compose'
DOCKER_COMPOSE_CMD=docker compose -f $(DOCKER_COMPOSE_FILE)

.PHONY: dev-run dev-shell dev-build dev-clean dev-stop

dev-run:
	@echo "Starting the development environment..."
	$(DOCKER_COMPOSE_CMD) up --build

dev-shell: 
	@echo "Opening a shell in the container..."
	$(DOCKER_COMPOSE_CMD) run --rm --service-ports api shell-mode

dev-build:
	$(DOCKER_COMPOSE_CMD) build

dev-stop:
	$(DOCKER_COMPOSE_CMD) stop

dev-clean:
	$(DOCKER_COMPOSE_CMD) down --remove-orphans --volumes

init:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

migrate:
	$(DJANGO_MANAGE) migrate

makemigrations:
	$(DJANGO_MANAGE) makemigrations

run:
	$(DJANGO_MANAGE) runserver 0.0.0.0:8000

superuser:
	$(DJANGO_MANAGE) createsuperuser

test:
	$(DJANGO_MANAGE) test

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +

setup: clean migrate makemigrations superuser