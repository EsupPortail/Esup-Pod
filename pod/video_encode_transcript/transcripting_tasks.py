"""Esup-Pod transcripting tasks."""

# pip3 install celery==5.4.0
# pip3 install webvtt-py
# pip3 install redis==4.5.4
from celery import Celery
from tempfile import NamedTemporaryFile
import logging
import os
import requests

# call local settings directly
# no need to load pod application to send statement
try:
    from ..custom import settings_local
except ImportError:
    from .. import settings as settings_local

logger = logging.getLogger(__name__)

EMAIL_HOST = getattr(settings_local, "EMAIL_HOST", "")
DEFAULT_FROM_EMAIL = getattr(settings_local, "DEFAULT_FROM_EMAIL", "")
ADMINS = getattr(settings_local, "ADMINS", ())
DEBUG = getattr(settings_local, "DEBUG", True)
TEST_REMOTE_ENCODE = getattr(settings_local, "TEST_REMOTE_ENCODE", False)

admins_email = [ad[1] for ad in ADMINS]

if DEBUG:
    logger.setLevel(logging.DEBUG)

smtp_handler = logging.handlers.SMTPHandler(
    mailhost=EMAIL_HOST,
    fromaddr=DEFAULT_FROM_EMAIL,
    toaddrs=admins_email,
    subject="[POD TRANSCRIPT] Transcripting Log Mail",
)
if not TEST_REMOTE_ENCODE:
    logger.addHandler(smtp_handler)

POD_API_URL = getattr(settings_local, "POD_API_URL", "")
POD_API_TOKEN = getattr(settings_local, "POD_API_TOKEN", "")

ENCODING_TRANSCODING_CELERY_BROKER_URL = getattr(
    settings_local, "ENCODING_TRANSCODING_CELERY_BROKER_URL", ""
)

transcripting_app = Celery(
    "transcripting_tasks", broker=ENCODING_TRANSCODING_CELERY_BROKER_URL
)
transcripting_app.conf.task_routes = {
    "pod.video_encode_transcript.transcripting_tasks.*": {"queue": "transcripting"}
}
transcripting_app.autodiscover_tasks(packages=None, related_name="", force=False)


# celery \
# -A pod.video_encode_transcript.transcripting_tasks worker \
# -l INFO -Q transcripting
@transcripting_app.task(bind=True)
def start_transcripting_task(self, video_id, mp3filepath, duration, lang):
    """Start the transcripting of the video."""
    from .transcript_model import start_transcripting
    from ..main.settings import MEDIA_ROOT

    print("Start the transcripting of the video %s" % video_id)
    print(video_id, mp3filepath, duration, lang)
    msg, text_webvtt = start_transcripting(mp3filepath, duration, lang)
    print("End of the transcripting of the video")
    media_temp_dir = os.path.join(MEDIA_ROOT, "temp")
    if not os.path.exists(media_temp_dir):
        os.mkdir(media_temp_dir)
    temp_vtt_file = NamedTemporaryFile(dir=media_temp_dir, delete=False, suffix=".vtt")
    text_webvtt.save(temp_vtt_file.name)
    print("End of the transcoding of the video")
    Headers = {"Authorization": "Token %s" % POD_API_TOKEN}
    url = POD_API_URL.strip("/") + "/store_remote_transcripted_video/?id=%s" % video_id
    data = {"video_id": video_id, "msg": msg, "temp_vtt_file": temp_vtt_file.name}
    msg = "Task id : %s\n" % self.request.id
    try:
        response = requests.post(url, json=data, headers=Headers)
        if response.status_code != 200:
            msg += "Calling store remote transcoding error: {} {}".format(
                response.status_code, response.reason
            )
            logger.error(msg + "\n" + str(response.content))
        else:
            logger.info(msg + "Call importing transcript task ok")
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.InvalidURL,
        requests.exceptions.Timeout,
    ) as exception:
        msg += "Exception on start_transcripting_task: {}".format(type(exception).__name__)
        msg += "\nURL: %s" % url
        msg += "\nException message: {}".format(exception)
        logger.error(msg)
