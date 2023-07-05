from django.conf import settings
from django.core.files import File
from pod.completion.models import Track
from pod.main.tasks import task_start_transcript

from .utils import (
    send_email,
    send_email_transcript,
    change_encoding_step,
    add_encoding_log,
)
from ..video.models import Video
import importlib.util

if (
    importlib.util.find_spec("vosk") is not None
    or importlib.util.find_spec("stt") is not None
):
    from .transcript_model import start_transcripting

import os
import time

from tempfile import NamedTemporaryFile

import threading
import logging

DEBUG = getattr(settings, "DEBUG", False)

if getattr(settings, "USE_PODFILE", False):
    __FILEPICKER__ = True
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder
else:
    __FILEPICKER__ = False
    from pod.main.models import CustomFileModel

EMAIL_ON_TRANSCRIPTING_COMPLETION = getattr(
    settings, "EMAIL_ON_TRANSCRIPTING_COMPLETION", True
)
TRANSCRIPTION_MODEL_PARAM = getattr(settings, "TRANSCRIPTION_MODEL_PARAM", False)
USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    TRANSCRIPTION_TYPE = getattr(settings, "TRANSCRIPTION_TYPE", "VOSK")
TRANSCRIPTION_NORMALIZE = getattr(settings, "TRANSCRIPTION_NORMALIZE", False)
CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)

USE_DISTANT_ENCODING_TRANSCODING = getattr(
    settings, "USE_DISTANT_ENCODING_TRANSCODING", False
)
if USE_DISTANT_ENCODING_TRANSCODING:
    from .transcripting_tasks import start_transcripting_task

log = logging.getLogger(__name__)

"""
TO TEST IN THE SHELL -->
from pod.video.transcript import *
stt_model = get_model("fr")
msg, webvtt, all_text = main_stt_transcript(
    "/test/audio_192k_pod.mp3", # file
    177, # file duration
    stt_model # model stt loaded
)
print(webvtt)
"""


# ##########################################################################
# TRANSCRIPT VIDEO: THREAD TO LAUNCH TRANSCRIPT
# ##########################################################################
def start_transcript(video_id, threaded=True):
    """
    Main function call to start transcript.
    Will launch transcript mode depending on configuration.
    """
    if threaded:
        if CELERY_TO_ENCODE:
            task_start_transcript.delay(video_id)
        else:
            log.info("START TRANSCRIPT VIDEO %s" % video_id)
            t = threading.Thread(target=main_threaded_transcript, args=[video_id])
            t.setDaemon(True)
            t.start()
    else:
        main_threaded_transcript(video_id)


def main_threaded_transcript(video_to_encode_id):
    """
    Main function to transcript.
    Will check all configuration and file and launch transcript.
    """
    change_encoding_step(video_to_encode_id, 5, "transcripting audio")

    video_to_encode = Video.objects.get(id=video_to_encode_id)

    msg = ""
    lang = video_to_encode.transcript
    # check if TRANSCRIPTION_MODEL_PARAM [lang] exist
    if not TRANSCRIPTION_MODEL_PARAM[TRANSCRIPTION_TYPE].get(lang):
        msg += "\n no stt model found for lang:%s." % lang
        msg += "Please add it in TRANSCRIPTION_MODEL_PARAM."
        change_encoding_step(video_to_encode.id, -1, msg)
        send_email(msg, video_to_encode.id)
    else:
        mp3file = (
            video_to_encode.get_video_mp3().source_file
            if video_to_encode.get_video_mp3()
            else None
        )
        if mp3file is None:
            msg += "\n no mp3 file found for video :%s." % video_to_encode.id
            change_encoding_step(video_to_encode.id, -1, msg)
            send_email(msg, video_to_encode.id)
        else:
            mp3filepath = mp3file.path
            if USE_DISTANT_ENCODING_TRANSCODING:
                start_transcripting_task.delay(
                    video_to_encode.id, mp3filepath, video_to_encode.duration, lang
                )
            else:
                msg, webvtt = start_transcripting(
                    mp3filepath, video_to_encode.duration, lang
                )
                save_vtt_and_notify(video_to_encode, msg, webvtt)
    add_encoding_log(video_to_encode.id, msg)


def save_vtt_and_notify(video_to_encode, msg, webvtt):
    """Call save vtt file function and notify by mail at the end."""
    msg += saveVTT(video_to_encode, webvtt)
    change_encoding_step(video_to_encode.id, 0, "done")
    # envois mail fin transcription
    if EMAIL_ON_TRANSCRIPTING_COMPLETION:
        send_email_transcript(video_to_encode)
    add_encoding_log(video_to_encode.id, msg)


def saveVTT(video, webvtt):
    """Save webvtt file with the video."""
    msg = "\nSAVE TRANSCRIPT WEBVTT : %s" % time.ctime()
    lang = video.transcript
    temp_vtt_file = NamedTemporaryFile(suffix=".vtt")
    webvtt.save(temp_vtt_file.name)
    if webvtt.captions:
        msg += "\nstore vtt file in bdd with CustomFileModel model file field"
        if __FILEPICKER__:
            videodir, created = UserFolder.objects.get_or_create(
                name="%s" % video.slug, owner=video.owner
            )
            """
            previousSubtitleFile = CustomFileModel.objects.filter(
                name__startswith="subtitle_%s" % lang,
                folder=videodir,
                created_by=video.owner
            )
            """
            # for subt in previousSubtitleFile:
            #     subt.delete()
            subtitleFile, created = CustomFileModel.objects.get_or_create(
                name="subtitle_%s_%s" % (lang, time.strftime("%Y%m%d-%H%M%S")),
                folder=videodir,
                created_by=video.owner,
            )
            if subtitleFile.file and os.path.isfile(subtitleFile.file.path):
                os.remove(subtitleFile.file.path)
        else:
            subtitleFile, created = CustomFileModel.objects.get_or_create()

        subtitleFile.file.save(
            "subtitle_%s_%s.vtt" % (lang, time.strftime("%Y%m%d-%H%M%S")),
            File(temp_vtt_file),
        )
        msg += "\nstore vtt file in bdd with Track model src field"

        subtitleVtt, created = Track.objects.get_or_create(video=video, lang=lang)
        subtitleVtt.src = subtitleFile
        subtitleVtt.lang = lang
        subtitleVtt.save()
    else:
        msg += "\nERROR SUBTITLES Output size is 0"
    return msg
