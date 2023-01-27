echo "Launching commandes into pod-dev"
mkdir -p pod/node_modules
mkdir -p pod/db_migrations && touch pod/db_migrations/__init__.py
ln -fs /tmp/node_modules/* pod/node_modules
until nc -z elasticsearch 9200; do echo waiting for elasticsearch; sleep 10; done;
BDD_EXISTS=/usr/src/app/pod/db.sqlite3
if test ! -f "$BDD_EXISTS"; then
    echo "$BDD_EXISTS does not exist."
    python3 manage.py create_pod_index
    curl -XGET "elasticsearch:9200/pod/_search"
    python3 manage.py collectstatic --no-input --clear
    make createDB
    python3 manage.py createsuperuser --noinput
else
    echo "$BDD_EXISTS exist."
fi
python3 manage.py runserver 0.0.0.0:8080 --insecure
sleep infinity