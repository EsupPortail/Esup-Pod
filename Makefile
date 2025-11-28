# Variables
PYTHON=python3
DJANGO_MANAGE=$(PYTHON) manage.py

# Environnement
init:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

# Base de données
migrate:
	$(DJANGO_MANAGE) migrate

makemigrations:
	$(DJANGO_MANAGE) makemigrations

# Lancer le serveur
run:
	$(DJANGO_MANAGE) runserver 0.0.0.0:8000

# Créer un superuser
superuser:
	$(DJANGO_MANAGE) createsuperuser

# Lancer les tests
test:
	$(DJANGO_MANAGE) test

# Nettoyage
clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} +

# Setup complet (installation + migrations)
setup: clean migrate makemigrations superuser
