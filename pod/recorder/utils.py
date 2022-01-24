import time
import os
from .models import Recording
from django.conf import settings


def add_comment(recording_id, comment):
    recording = Recording.objects.get(id=recording_id)
    recording.comment = "%s\n%s" % (recording.comment, comment)
    recording.save()


def studio_clean_old_files():
    folder_to_clean = os.path.join(settings.MEDIA_ROOT, "opencast-files")
    now = time.time()

    for f in os.listdir(folder_to_clean):
        f = os.path.join(folder_to_clean, f)
        if os.stat(f).st_mtime < now - 7 * 86400:
            if os.path.isfile(f):
                os.remove(f)
