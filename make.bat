@echo off
for /f "delims=" %%a in (.env.dev) do call set %%a
if /i "%1"=="docker-build" (
  echo "Suppression du repertoire node_modules"
  rmdir /s /q .\pod\node_modules
  echo "Suppression du repertoire node_modules"
  rmdir /s /q .\pod\static
  echo "Suppression du repertoire log"
  rmdir /s /q .\pod\log
  echo "Chargement des variables d'environnement depuis le fichier .env.dev"
  for /f "delims=" %%a in (.env.dev) do call set %%a
  echo "Debut du build"
  docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod build --build-arg ELASTICSEARCH_VERSION=%ELASTICSEARCH_TAG% --build-arg NODE_VERSION=%NODE_TAG% --build-arg PYTHON_VERSION=%PYTHON_TAG% --no-cache
  echo "Debut du start"
  docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod up
  echo "Vous devriez obtenir ce message une fois esup-pod lance"
  echo "pod-dev-with-volumes        | Superuser created successfully."
  echo "Fin du build"
) else if /i "%1"=="docker-start" (
  echo "Debut du start"
  docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod up
  echo "Fin du start"
) else if /i "%1"=="docker-stop" (
  echo "Debut du stop"
  docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod down -v
  echo "Fin du stop"
) else if /i "%1"=="docker-reset" (
  echo "Debut du reset"
  docker-compose -f ./docker-compose-dev-with-volumes.yml -p esup-pod down -v
  echo "Suppression du repertoire node_modules"
  rmdir /s /q .\pod\node_modules
  echo "Suppression du repertoire node_modules"
  rmdir /s /q .\pod\static
  echo "Suppression du repertoire log"
  rmdir /s /q .\pod\log
  echo "Suppression du repertoire db_migrations"
  rmdir /s /q .\pod\db_migrations
  echo "Suppression du repertoire db.sqlite3"
  del /s /q .\pod\db.sqlite3
  echo "Suppression du repertoire media"
  rmdir /s /q .\pod\media
  echo "Fin du reset"
) else (
  echo "Mauvaise syntaxe"
)
