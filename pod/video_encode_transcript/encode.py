"""Esup-Pod module to handle video encoding with CPU."""

from django.conf import settings
from webpush.models import PushInformation

from pod.video.models import Video
from .Encoding_video_model import Encoding_video_model
from .encoding_studio import start_encode_video_studio
from .models import EncodingLog

from pod.cut.models import CutVideo
from pod.dressing.models import Dressing
from pod.dressing.utils import get_dressing_input
from pod.main.tasks import task_start_encode, task_start_encode_studio
from pod.recorder.models import Recording
from .encoding_settings import FFMPEG_DRESSING_INPUT
from .utils import (
    change_encoding_step,
    check_file,
    add_encoding_log,
    send_email,
    send_email_encoding,
    send_email_recording,
    send_notification_encoding,
    time_to_seconds,
)
import logging
import time
import threading

__license__ = "LGPL v3"
log = logging.getLogger(__name__)

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
USE_NOTIFICATIONS = getattr(settings, "USE_NOTIFICATIONS", False)
if USE_TRANSCRIPTION:
    from . import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)
EMAIL_ON_ENCODING_COMPLETION = getattr(settings, "EMAIL_ON_ENCODING_COMPLETION", True)

USE_REMOTE_ENCODING_TRANSCODING = getattr(
    settings, "USE_REMOTE_ENCODING_TRANSCODING", False
)
if USE_REMOTE_ENCODING_TRANSCODING:
    from .encoding_tasks import start_encoding_task
    from .encoding_tasks import start_studio_task

FFMPEG_DRESSING_INPUT = getattr(settings, "FFMPEG_DRESSING_INPUT", FFMPEG_DRESSING_INPUT)

# ##########################################################################
# ENCODE VIDEO: THREAD TO LAUNCH ENCODE
# ##########################################################################

# Disable for the moment, will be reactivated in future version


def start_encode(video_id: int, threaded=True) -> None:
    """Start video encoding."""
    if threaded:
        if CELERY_TO_ENCODE:
            task_start_encode.delay(video_id)
        else:
            log.info("START ENCODE VIDEO ID %s" % video_id)
            t = threading.Thread(target=encode_video, args=[video_id])
            t.daemon = True
            t.start()
    else:
        encode_video(video_id)


def start_encode_studio(
    recording_id, video_output, videos, subtime, presenter, threaded=True
) -> None:
    """Start studio encoding."""
    if threaded:
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
            t.daemon = True
            t.start()
    else:
        encode_video_studio(recording_id, video_output, videos, subtime, presenter)


def encode_video_studio(recording_id, video_output, videos, subtime, presenter) -> None:
    """ENCODE STUDIO: MAIN FUNCTION."""
    msg = ""
    if USE_REMOTE_ENCODING_TRANSCODING:
        start_studio_task.delay(recording_id, video_output, videos, subtime, presenter)
    else:
        msg = start_encode_video_studio(video_output, videos, subtime, presenter)
        store_encoding_studio_info(recording_id, video_output, msg)


def store_encoding_studio_info(recording_id, video_output, msg) -> None:
    recording = Recording.objects.get(id=recording_id)
    recording.comment += msg
    recording.save()
    if check_file(video_output):
        from pod.recorder.plugins.type_studio import save_basic_video

        video = save_basic_video(recording, video_output)
        encode_video(video.id)
    else:
        msg = "Wrong file or path:\n%s" % video_output
        send_email_recording(msg, recording_id)


def encode_video(video_id: int) -> None:
    """ENCODE VIDEO: MAIN FUNCTION."""
    start = "Start at: %s" % time.ctime()

    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.encoding_in_progress = True
    video_to_encode.save()

    if not check_file(video_to_encode.video.path):
        msg = "Wrong file or path:\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)
        return

    change_encoding_step(video_id, 0, "start")
    # start and stop cut?
    encoding_video = get_encoding_video(video_to_encode)
    encoding_video.add_encoding_log("start_time", "", True, start)
    change_encoding_step(video_id, 1, "remove old data")
    encoding_video.remove_old_data()

    if USE_REMOTE_ENCODING_TRANSCODING:
        change_encoding_step(video_id, 2, "start remote encoding")
        dressing = None
        dressing_input = ""
        if Dressing.objects.filter(videos=video_to_encode).exists():
            dressing = Dressing.objects.get(videos=video_to_encode)
            if dressing:
                dressing_input = get_dressing_input(dressing, FFMPEG_DRESSING_INPUT)
        start_encoding_task.delay(
            encoding_video.id,
            encoding_video.video_file,
            encoding_video.cutting_start,
            encoding_video.cutting_stop,
            json_dressing=dressing.to_json() if dressing else None,
            dressing_input=dressing_input,
        )
    else:
        change_encoding_step(video_id, 2, "start standard encoding")
        encoding_video.start_encode()
        final_video = store_encoding_info(video_id, encoding_video)

        if encoding_video.error_encoding:
            enc_log, created = EncodingLog.objects.get_or_create(video=final_video)
            msg = "Error during video `%s` encoding." % video_id
            if created is False:
                msg += " See log at:\n%s" % enc_log.logfile.url
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)
        else:
            end_of_encoding(final_video)


def store_encoding_info(video_id: int, encoding_video: Encoding_video_model) -> Video:
    """Store all encoding file and informations from encoding tasks."""
    change_encoding_step(video_id, 3, "store encoding info")
    final_video = encoding_video.store_json_info()
    final_video.is_video = final_video.get_video_m4a() is None
    final_video.encoding_in_progress = False
    final_video.save()
    return final_video


def get_encoding_video(video_to_encode: Video) -> Encoding_video_model:
    """Get the encoding video object from video."""
    dressing = None
    dressing_input = ""
    if Dressing.objects.filter(videos=video_to_encode).exists():
        dressing = Dressing.objects.get(videos=video_to_encode)
        if dressing:
            dressing_input = get_dressing_input(dressing, FFMPEG_DRESSING_INPUT)

    if CutVideo.objects.filter(video=video_to_encode).exists():
        cut = CutVideo.objects.get(video=video_to_encode)
        cut_start = time_to_seconds(cut.start)
        cut_end = time_to_seconds(cut.end)
        encoding_video = Encoding_video_model(
            video_to_encode.id,
            video_to_encode.video.path,
            cut_start,
            cut_end,
            json_dressing=dressing.to_json() if dressing else None,
            dressing_input=dressing_input,
        )
        return encoding_video

    return Encoding_video_model(
        video_to_encode.id,
        video_to_encode.video.path,
        0,
        0,
        json_dressing=dressing.to_json() if dressing else None,
        dressing_input=dressing_input,
    )


def end_of_encoding(video: Video) -> None:
    """Notify user at the end of encoding & call transcription."""
    if (
        USE_NOTIFICATIONS
        and video.owner.owner.accepts_notifications
        and PushInformation.objects.filter(user=video.owner).exists()
    ):
        send_notification_encoding(video)
    if EMAIL_ON_ENCODING_COMPLETION:
        send_email_encoding(video)

    transcript_video(video.id)
    change_encoding_step(video.id, 0, "end of encoding")


def transcript_video(video_id: int) -> None:
    """Transcript video audio to text."""
    video = Video.objects.get(id=video_id)
    if USE_TRANSCRIPTION and video.transcript not in ["", "0", "1"]:
        change_encoding_step(video_id, 4, "transcript video")
        start_transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
        start_transcript_video(video_id, False)
