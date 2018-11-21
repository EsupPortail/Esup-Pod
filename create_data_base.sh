find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata pod/video/fixtures/initial_data.json
python manage.py loaddata pod/main/fixtures/initial_data.json
