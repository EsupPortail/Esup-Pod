import threading
import logging

from django.conf import settings
from pod.video.bbb import start_bbb_encode

BBB_ENCODE_MEETING = getattr(settings, "BBB_ENCODE_MEETING", start_bbb_encode)

log = logging.getLogger(__name__)


# Process that allows to create a video file
# from a BigBlueButton presentation
def process(recording):
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=bbb_encode_recording, args=[recording])
    t.setDaemon(True)
    t.start()


# Create a video file from a BigBlueButton presentation
def bbb_encode_recording(recording):
    BBB_ENCODE_MEETING(recording.id)
