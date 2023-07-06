#!/bin/sh
echo "Launching commands into pod-dev"
until nc -z pod-back 8080; do echo waiting for pod-back; sleep 10; done;
# Serveur xAPI
celery -A pod.xapi.xapi_tasks worker -l INFO -Q xapi --concurrency 1 -n xapi
sleep infinity
