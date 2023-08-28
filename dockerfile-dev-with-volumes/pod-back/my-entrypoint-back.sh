#!/bin/sh
echo "Launching commands into pod-dev"
mkdir -p pod/node_modules
mkdir -p pod/db_migrations && touch pod/db_migrations/__init__.py
ln -fs /tmp/node_modules/* pod/node_modules
until nc -z elasticsearch 9200; do echo waiting for elasticsearch; sleep 10; done;
# Mise en route
# Base de données SQLite intégrée
BDD_FILE=/usr/src/app/pod/db.sqlite3
if test ! -f "$BDD_FILE"; then
    echo "$BDD_FILE does not exist."
    python3 manage.py create_pod_index
    curl -XGET "elasticsearch:9200/pod/_search"
    # Deployez les fichiers statiques
    python3 manage.py collectstatic --no-input --clear
    # Lancez le script présent à la racine afin de créer les fichiers de migration, puis de les lancer pour créer la base de données SQLite intégrée.
    make createDB
    # SuperUtilisateur
    # Il faut créer un premier utilisateur qui aura tous les pouvoirs sur votre instance.
    python3 manage.py createsuperuser --noinput
else
    echo "$BDD_FILE exist."
fi
# Serveur de développement
# Le serveur de développement permet de tester vos futures modifications facilement.
# N'hésitez pas à lancer le serveur de développement pour vérifier vos modifications au fur et à mesure.
# À ce niveau, vous devriez avoir le site en français et en anglais et voir l'ensemble de la page d'accueil.
celery -A pod.video_encode_transcript.importing_tasks worker -l INFO -Q importing --concurrency 1 --detach -n import_encode
celery -A pod.video_encode_transcript.importing_transcript_tasks worker -l INFO -Q importing_transcript --concurrency 1 --detach -n import_transcript
python3 manage.py runserver 0.0.0.0:8080 --insecure
sleep infinity
