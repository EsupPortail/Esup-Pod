from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pod.settings')

app = Celery('pod')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(['pod.video'])

app.conf.beat_schedule = {
    'publish-scheduled-videos-every-minute': {
        'task': 'pod.video.tasks.publish_scheduled_videos',
        'schedule': 60.0,  
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')