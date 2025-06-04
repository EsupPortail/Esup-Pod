#!/bin/sh
echo "Launching commands into pod-dev"
until nc -z pod.localhost 8000; do echo waiting for pod-back; sleep 10; done;
# Worker ActivityPub
celery --app pod.activitypub.tasks worker --loglevel INFO --queues activitypub --concurrency 1 --hostname activitypub
sleep infinity
