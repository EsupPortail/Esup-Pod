#!/bin/sh
INSTANCE="${POD_INSTANCE:-pod}"
PORT="${POD_PORT:-8000}"
echo "Launching commands into ${INSTANCE}-dev"
mkdir -p pod/node_modules
mkdir -p pod/db_migrations && touch pod/db_migrations/__init__.py
ln -fs /tmp/node_modules/* pod/node_modules
# Mise en route
# Base de données SQLite intégrée
INIT_FILE="/usr/src/app/pod/.${INSTANCE}.initialized"
if test ! -f "$INIT_FILE"; then
    echo "$INIT_FILE does not exist."
    python3 manage.py create_pod_index
    curl -XGET "elasticsearch.localhost:9200/${INSTANCE}/_search"
    # Deployez les fichiers statiques
    python3 manage.py collectstatic --no-input --clear --verbosity 0
    # Lancez le script présent à la racine afin de créer les fichiers de migration, puis de les lancer pour créer la base de données SQLite intégrée.
    make createDB
    # SuperUtilisateur
    # Il faut créer un premier utilisateur qui aura tous les pouvoirs sur votre instance.
    python3 manage.py createsuperuser --noinput
    touch "$INIT_FILE"
else
    echo "$INIT_FILE exist."
fi
# Serveur de développement
# Le serveur de développement permet de tester vos futures modifications facilement.
# N'hésitez pas à lancer le serveur de développement pour vérifier vos modifications au fur et à mesure.
# À ce niveau, vous devriez avoir le site en français et en anglais et voir l'ensemble de la page d'accueil.
python3 manage.py runserver "0.0.0.0:${PORT}" --insecure
sleep infinity
