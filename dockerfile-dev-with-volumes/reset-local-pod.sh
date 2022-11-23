
#!/bin/bash
set -xv
docker-compose -f ../docker-compose-dev-with-volumes.yml -p esup-pod down -v
sudo rm -rf ../pod/log
sudo rm -rf ../pod/media
sudo rm -rf ../pod/static
sudo rm -rf ../pod/node_modules
sudo rm -rf ../pod/db_migrations
sudo rm ../pod/db.sqlite3
sudo rm ../pod/yarn.lock
