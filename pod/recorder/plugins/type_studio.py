# type_studio.py

import threading
import logging
import datetime

from django.conf import settings
from ..utils import add_comment

DEFAULT_RECORDER_TYPE_ID = getattr(settings, "DEFAULT_RECORDER_TYPE_ID", 1)

ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")

log = logging.getLogger(__name__)


def process(recording):
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=encode_recording, args=[recording])
    t.setDaemon(True)
    t.start()


def encode_recording(recording):
    recording.comment = ""
    recording.save()
    add_comment(recording.id, "Start at %s\n--\n" % datetime.datetime.now())
    print("encode_recording")
