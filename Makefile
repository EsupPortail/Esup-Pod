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
	# Première installation de pod
	make upgrade
	make createDB

upgrade:
	# Mise à jour de Pod
	git pull
	python3 -m pip install -r requirements.txt
	make updatedb
	make migrate

createDB:
	# Création des données initiales dans la BDD
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc"  -delete
	make updatedb
	make migrate
	python3 manage.py loaddata pod/video/fixtures/initial_data.json
	python3 manage.py loaddata pod/main/fixtures/initial_data.json

lang:
	# Mise à jour des fichiers de langue
	echo "Processing python files..."
	python3 manage.py makemessages --all
	echo "Processing javascript files..."
	django-admin makemessages -d djangojs -l fr -l nl -i "*.min.js" -i "pod/static/*"

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
