#!/bin/sh
echo "Launching commands into pod-dev"
# Serveur d'encodage
watchmedo auto-restart --directory=/usr/src/app --pattern=*.py --recursive -- \
celery -A pod.video_encode_transcript.encoding_tasks worker -l INFO -Q encoding --concurrency 1 -n encode
sleep infinity
