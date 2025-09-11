"""Esup-Pod Celery app."""

import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pod.settings")

try:
    from pod.custom import settings_local
except ImportError:
    from pod import settings as settings_local

INSTANCE = getattr(settings_local, "INSTANCE", None)

app = Celery("pod_project")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(packages=["pod.main"], related_name="tasks", force=False)
app.conf.task_routes = {
    "pod.main.tasks.*": {"queue": "celery"},
    "pod.main.celery.*": {"queue": "celery"},
}
if INSTANCE:
    app.conf.broker_transport_options = {"global_keyprefix": INSTANCE}


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
