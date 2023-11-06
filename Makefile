# Utilitaires shell pour Esup-Pod

# Ne pas oublier de lancer un `workon django_pod` avant toute commande.
# Lancer via `make $cmd`
# (en remplacant $cmd par une commande ci-dessous)


# Affiche la liste des commandes disponibles
help:
	echo "Syntax: [make target] where target is in this list:"
	@awk '/^#/{c=substr($$0,3);next}c&&/^[[:alpha:]][[:alnum:]_-]+:/{print substr($$1,1,index($$1,":")),c}1{c=0}' $(MAKEFILE_LIST) | column -s: -t

# Démarre le serveur de test
start:
	(sleep 15 ; open http://localhost:9090) &
	python3 manage.py runserver localhost:9090 --insecure
	# --insecure let serve static files even when DEBUG=False

# Démarre le serveur de test en https auto-signé
starts:
	# nécessite les django-extensions
	# cf https://timonweb.com/django/https-django-development-server-ssl-certificate/
	(sleep 15 ; open https://localhost:8000) &
	python3 manage.py runserver_plus --cert-file cert.pem --key-file key.pem

# Première installation de pod (BDD SQLite intégrée)
install:
	npm install -g yarn
	cd pod; yarn
	make upgrade
	make createDB

# Mise à jour de Pod
upgrade:
	git pull origin master
	python3 -m pip install -r requirements.txt
	make updatedb
	make migrate
	make statics

# Création des données initiales dans la BDD SQLite intégrée
createDB:
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	make updatedb
	make migrate
	python3 manage.py loaddata initial_data

# Mise à jour des fichiers de langue
lang:
	echo "Processing python files..."
	python3 manage.py makemessages --all -i "opencast-studio/*" -i "pod/custom/settings_local.py" --add-location=file
	echo "Processing javascript files..."
	python3 manage.py makemessages -d djangojs -l fr -l nl -i "*.min.js" -i "pod/static/*" -i "opencast-studio/*" -i "*/node_modules/*"  -i "node_modules/*" --add-location=file

#compilation des fichiers de langue
compilelang:
	python3 manage.py compilemessages -l fr -l nl

# Look for changes to apply in DB
updatedb:
	python3 manage.py makemigrations

# Apply all changes in DB
migrate:
	python3 manage.py migrate

# Launch all unit tests.
tests:
	coverage run --source='.' manage.py test --settings=pod.main.test_settings
	coverage html

# Ensure coherence of all code style
pystyle:
	flake8

# Collects all static files inside all apps and put a copy inside the static directory declared in settings.py
statics:
	cd pod; yarn install; yarn upgrade
	# --clear Clear the existing files before trying to copy or link the original file.
	python3 manage.py collectstatic --clear

# Generate configuration docs in .MD format
createconfigs:
	python3 manage.py createconfiguration fr
	python3 manage.py createconfiguration en

# -- Docker
# Use for docker run and docker exec commands
-include .env.dev
export
COMPOSE = docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod
COMPOSE_FULL = docker-compose -f ./docker-compose-full-dev-with-volumes.yml -p esup-pod
DOCKER_LOGS = docker logs -f

#docker-start-build:
#	# Démarre le serveur de test en recompilant les conteneurs de la stack
#	# (Attention, il a été constaté que sur un mac, le premier lancement peut prendre plus de 5 minutes.)
#	@$(COMPOSE) up --build
#	# Vous devriez obtenir ce message une fois esup-pod lancé
#	# $ pod-dev-with-volumes        | Superuser created successfully.

# Display app logs (follow mode)
docker-logs:
	@$(DOCKER_LOGS) pod-dev-with-volumes

# Display environment variables for docker
echo-env:
	@echo ELASTICSEARCH_TAG=$(ELASTICSEARCH_TAG)
	@echo PYTHON_TAG=$(PYTHON_TAG)
	@echo DOCKER_ENV=$(DOCKER_ENV)

# Démarre le serveur de test en recompilant les conteneurs de la stack
docker-build:
	# (Attention, il a été constaté que sur un mac, le premier lancement peut prendre plus de 5 minutes.)
	# N'oubliez pas de supprimer :
	# sudo rm -rf ./pod/log
	sudo rm -rf ./pod/log
	# sudo rm -rf ./pod/static
	sudo rm -rf ./pod/static
	# sudo rm -rf ./pod/node_modules
	sudo rm -rf ./pod/node_modules
ifeq ($(DOCKER_ENV), full)
	@$(COMPOSE_FULL) build --build-arg ELASTICSEARCH_VERSION=$(ELASTICSEARCH_TAG) --build-arg NODE_VERSION=$(NODE_TAG) --build-arg PYTHON_VERSION=$(PYTHON_TAG) --no-cache
	@$(COMPOSE_FULL) up
else
	@$(COMPOSE) build --build-arg ELASTICSEARCH_VERSION=$(ELASTICSEARCH_TAG) --build-arg NODE_VERSION=$(NODE_TAG) --build-arg PYTHON_VERSION=$(PYTHON_TAG) --no-cache
	@$(COMPOSE) up
endif
	# Vous devriez obtenir ce message une fois esup-pod lancé
	# $ pod-dev-with-volumes        | Superuser created successfully.

# Démarre le serveur de test
docker-start:
	# (Attention, il a été constaté que sur un mac, le premier lancement peut prendre plus de 5 minutes.)
ifeq ($(DOCKER_ENV), full)
	@$(COMPOSE_FULL) up
else
	@$(COMPOSE) up
endif
	# Vous devriez obtenir ce message une fois esup-pod lancé
	# $ pod-dev-with-volumes        | Superuser created successfully.

# Arrête le serveur de test
docker-stop:
ifeq ($(DOCKER_ENV), full)
	@$(COMPOSE_FULL) down -v
else
	@$(COMPOSE) down -v
endif
# Arrête le serveur de test et supprime les fichiers générés
docker-reset:
ifeq ($(DOCKER_ENV), full)
	@$(COMPOSE_FULL) down -v
else
	@$(COMPOSE) down -v
endif
	# sudo rm -rf ./pod/log
	sudo rm -rf ./pod/log
	# sudo rm -rf ./pod/static
	sudo rm -rf ./pod/static
	# sudo rm -rf ./pod/node_modules
	sudo rm -rf ./pod/node_modules
	# sudo rm -rf ./pod/db_migrations
	sudo rm -rf ./pod/db_migrations
	# sudo rm -rf ./pod/db.sqlite3"
	sudo rm -rf ./pod/db.sqlite3
	# sudo rm -rf ./pod/media"
	sudo rm -rf ./pod/media
