---
layout: default
version: 4.x
lang: en
---

# Delete videos from recorders that have not been claimed for a defined period of time

> ⚠️ Script to be tested on a v4 Pod.

On our Pod, videos from recorders are claimed manually. We created this script to automatically delete unclaimed videos.

The script retrieves all videos from the recorder_recordingfiletreatment table. If the retention period has expired, the recording is deleted from the database as well as the video file.

**Add the retention period to the configuration file `custom/settings_local.py`**

```bash
RECORD_RETENTION = 30
```

**Create the file /pod/custom/management/commands/enregistrement.py**

```python
import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import translation, timezone
from pod.recorder.models import Recorder, Recording, RecordingFileTreatment
from datetime import timedelta, datetime
import logging

LANGUAGE_CODE = getattr(settings, ‘LANGUAGE_CODE’, ‘en’)

RECORD_RETENTION = getattr(
    settings, ‘RECORD_RETENTION’, ‘30’)

DEFAULT_RECORDER_PATH = getattr(settings, ‘DEFAULT_RECORDER_PATH’, ‘/data/ftp-pod/ftp/’)

log = logging.getLogger(__name__)
def checkRecordingRetention():
    if RecordingFileTreatment.objects.all().count() > 0:
        enregistrements = RecordingFileTreatment.objects.all()
        for enregistrement in enregistrements:
            print(enregistrement.file)
            if retention_depasee(enregistrement):
                print(« rétention dépassée »)
                supprimer_enregistrement(enregistrement)

def supprimer_enregistrement(enregistrement):
    if os.path.isfile(enregistrement.file):
        log.info("DELETE RECORD %s" % enregistrement.file)
        os.remove(enregistrement.file)
        enregistrement.delete()

def retention_depasee(enregistrement):
    resultat = False
    dateretention = enregistrement.date_added + timedelta(days=int(RECORD_RETENTION))
    print(dateretention)
    if dateretention < timezone.now():
        resultat = True
    return resultat

class Command(BaseCommand):
    valid_args = [« checkRecordingRetention »]

    def add_arguments(self, parser):
        parser.add_argument(« checkRecordingRetention », help="Deletes unclaimed records")

    def handle(self, *args, **options):
        translation.activate(LANGUAGE_CODE)
        if options[« checkRecordingRetention »]:
            checkRecordingRetention()
```

To run the command manually:

```bash
python manage.py recording checkRecordingRetention
```

To run the command via cron:

```bash
crontab -e

*/15 * * * * /usr/bin/bash -c 'export WORKON_HOME=/data/www/%userpod%/.virtualenvs; export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3.11; cd /data/www/%userpod%/django_projects/podv4; source /usr/bin/virtualenvwrapper.sh; workon django_pod; python manage.py recording checkRecordingRetention'
```
