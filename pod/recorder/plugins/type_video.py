# video type process
import threading
import logging
import datetime
import os

from django.conf import settings
from pod.video.models import Video, Type, get_storage_path_video
from pod.video.encode import start_encode

DEFAULT_RECORDER_TYPE_ID = getattr(
    settings, 'DEFAULT_RECORDER_TYPE_ID',
    1
)

ENCODE_VIDEO = getattr(settings,
                       'ENCODE_VIDEO',
                       start_encode)

log = logging.getLogger(__name__)


def process(recording):
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=encode_recording,
                         args=[recording])
    t.setDaemon(True)
    t.start()


def encode_recording(recording):
    video = Video()
    video.title = recording.title
    video.owner = recording.user
    video.type = Type.objects.get(id=DEFAULT_RECORDER_TYPE_ID)
    # gestion de la video
    storage_path = get_storage_path_video(
        video, os.path.basename(recording.source_file))
    dt = str(datetime.datetime.now())
    nom, ext = os.path.splitext(os.path.basename(recording.source_file))
    ext = ext.lower()
    video.video = os.path.join(
        os.path.dirname(storage_path), nom + "_" + dt.replace(" ", "_") + ext)
    # deplacement du fichier source vers destination
    os.rename(recording.source_file, video.video.path)
    video.save()
    ENCODE_VIDEO(video.id)
