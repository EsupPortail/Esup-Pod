
#!/bin/bash
set -xv
docker-compose -f ../docker-compose-dev-with-volumes.yml -p esup-pod down -v
sudo rm -rf ./pod/log
sudo rm -rf ./pod/static
sudo rm -rf ./pod/node_modules