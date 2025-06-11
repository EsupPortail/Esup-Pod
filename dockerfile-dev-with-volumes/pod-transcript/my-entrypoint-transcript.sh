#!/bin/sh
echo "Launching commands into pod-dev"
# Serveur d'encodage
watchmedo auto-restart --directory=/usr/src/app --pattern=*.py --recursive -- \
celery -A pod.video_encode_transcript.transcripting_tasks worker -l INFO -Q transcripting --concurrency 1 -n transcript
sleep infinity
