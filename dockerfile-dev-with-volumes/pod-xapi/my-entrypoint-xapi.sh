#!/bin/sh
echo "Launching commands into pod-dev"
# Serveur xAPI
watchmedo auto-restart --directory=/usr/src/app --pattern=*.py --recursive -- \
celery -A pod.xapi.xapi_tasks worker -l INFO -Q xapi --concurrency 1 -n xapi
sleep infinity
