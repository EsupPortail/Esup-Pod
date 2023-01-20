# Utilitaires shell pour Esup-Pod

# Ne pas oublier de lancer un `workon django_pod` avant toute commande.
# Lancer via `make $cmd`
# (en remplacant $cmd par une commande ci-dessous)

start:
	# Démarre le serveur de test
	(sleep 15 ; open http://localhost:8080) &
	python3 manage.py runserver localhost:8080 --insecure
	# --insecure let serve static files even when DEBUG=False

install:
	# Première installation de pod (BDD SQLite intégrée)
	npm install -g yarn
	cd pod; yarn
	make upgrade
	make createDB

upgrade:
	# Mise à jour de Pod
	git pull origin master
	python3 -m pip install -r requirements.txt
	make updatedb
	make migrate
	make statics

createDB:
	# Création des données initiales dans la BDD SQLite intégrée
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	make updatedb
	make migrate
	python3 manage.py loaddata pod/video/fixtures/initial_data.json
	python3 manage.py loaddata pod/main/fixtures/initial_data.json

lang:
	# Mise à jour des fichiers de langue
	echo "Processing python files..."
	python3 manage.py makemessages --all -i "opencast-studio/*"
	echo "Processing javascript files..."
	django-admin makemessages -d djangojs -l fr -l nl -i "*.min.js" -i "pod/static/*" -i "opencast-studio/*" -i "*/node_modules/*"

updatedb:
	# Look for changes to apply in DB
	python3 manage.py makemigrations

migrate:
	# Apply all changes in DB
	python3 manage.py migrate

tests:
	# Launch all unit tests.
	coverage run --source='.' manage.py test --settings=pod.main.test_settings
	coverage html

pystyle:
	# Ensure coherence of all code style
	flake8

statics:
	cd pod; yarn upgrade
	# Collects all static files inside all apps and put a copy inside the static directory declared in settings.py
	# --clear Clear the existing files before trying to copy or link the original file.
	python3 manage.py collectstatic --clear
