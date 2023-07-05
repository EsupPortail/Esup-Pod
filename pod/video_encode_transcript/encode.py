"""This module handles video encoding with CPU."""

from django.conf import settings
from pod.video.models import Video
from .Encoding_video_model import Encoding_video_model
from .encoding_studio import encode_video_studio

from pod.cut.models import CutVideo
from pod.main.tasks import task_start_encode, task_start_encode_studio
from .utils import (
    change_encoding_step,
    check_file,
    add_encoding_log,
    send_email,
    send_email_encoding,
    time_to_seconds,
)
import logging
import time
import threading

__license__ = "LGPL v3"
log = logging.getLogger(__name__)

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)

if USE_TRANSCRIPTION:
    from . import transcript
    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)
EMAIL_ON_ENCODING_COMPLETION = getattr(settings, "EMAIL_ON_ENCODING_COMPLETION", True)

USE_DISTANT_ENCODING_TRANSCODING = getattr(
    settings,
    "USE_DISTANT_ENCODING_TRANSCODING",
    False
)
if USE_DISTANT_ENCODING_TRANSCODING:
    from .encoding_tasks import start_encoding_task

# ##########################################################################
# ENCODE VIDEO: THREAD TO LAUNCH ENCODE
# ##########################################################################

# Disable for the moment, will be reactivated in future version
"""
def start_remote_encode(video_id):
    # load module here to prevent circular import
    from .remote_encode import remote_encode_video

    log.info("START ENCODE VIDEO ID %s" % video_id)
    t = threading.Thread(target=remote_encode_video, args=[video_id])
    t.setDaemon(True)
    t.start()
"""


def start_encode(video_id, threaded=True):
    """Start local encoding."""
    if threaded:
        if CELERY_TO_ENCODE:
            task_start_encode.delay(video_id)
        else:
            log.info("START ENCODE VIDEO ID %s" % video_id)
            t = threading.Thread(target=encode_video, args=[video_id])
            t.setDaemon(True)
            t.start()
    else:
        encode_video(video_id)


def start_encode_studio(recording_id, video_output, videos, subtime, presenter):
    """Start local encoding."""
    if CELERY_TO_ENCODE:
        task_start_encode_studio.delay(
            recording_id, video_output, videos, subtime, presenter
        )
    else:
        log.info("START ENCODE VIDEO ID %s" % recording_id)
        t = threading.Thread(
            target=encode_video_studio,
            args=[recording_id, video_output, videos, subtime, presenter],
        )
        t.setDaemon(True)
        t.start()


"""
def start_studio_remote_encode(recording_id, video_output, videos, subtime, presenter):
    # load module here to prevent circular import
    from .remote_encode import remote_encode_studio

    log.info("START ENCODE RECORDING ID %s" % recording_id)
    t = threading.Thread(
        target=remote_encode_studio,
        args=[recording_id, video_output, videos, subtime, presenter],
    )
    t.setDaemon(True)
    t.start()
"""


def encode_video(video_id):
    """ENCODE VIDEO: MAIN FUNCTION."""
    start = "Start at: %s" % time.ctime()

    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.encoding_in_progress = True
    video_to_encode.save()

    if not check_file(video_to_encode.video.path):
        msg = "Wrong file or path:" + "\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)
        return

    change_encoding_step(video_id, 0, "start")
    # start and stop cut ?
    encoding_video = get_encoding_video(video_to_encode)
    encoding_video.add_encoding_log("start_time", "", True, start)
    change_encoding_step(video_id, 1, "remove old data")
    encoding_video.remove_old_data()

    change_encoding_step(video_id, 2, "start encoding")
    if USE_DISTANT_ENCODING_TRANSCODING:
        start_encoding_task.delay(
            encoding_video.id,
            encoding_video.video_file,
            encoding_video.cutting_start,
            encoding_video.cutting_stop
        )
    else:
        encoding_video.start_encode()
        final_video = store_encoding_info(video_id, encoding_video)
        end_of_encoding(final_video)


def store_encoding_info(video_id, encoding_video):
    """Store all encoding file and informations from encoding tasks."""
    change_encoding_step(video_id, 3, "store encoding info")
    final_video = encoding_video.store_json_info()
    final_video.is_video = final_video.get_video_m4a() is None
    final_video.encoding_in_progress = False
    final_video.save()
    return final_video


def get_encoding_video(video_to_encode):
    """Get the encoding video object from video."""
    if CutVideo.objects.filter(video=video_to_encode).exists():
        cut = CutVideo.objects.get(video=video_to_encode)
        cut_start = time_to_seconds(cut.start)
        cut_end = time_to_seconds(cut.end)
        encoding_video = Encoding_video_model(
            video_to_encode.id, video_to_encode.video.path, cut_start, cut_end
        )
        return encoding_video
    return Encoding_video_model(video_to_encode.id, video_to_encode.video.path)


def end_of_encoding(video):
    """Send mail at the end of encoding, call transcription."""
    if EMAIL_ON_ENCODING_COMPLETION:
        send_email_encoding(video)

    transcript_video(video.id)
    change_encoding_step(video.id, 0, "end of encoding")


def transcript_video(video_id):
    """Transcript video audio to text."""
    video = Video.objects.get(id=video_id)
    if USE_TRANSCRIPTION and video.transcript not in ["", "0", "1"]:
        change_encoding_step(video_id, 4, "transcript video")
        start_transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
        start_transcript_video(video_id, False)
