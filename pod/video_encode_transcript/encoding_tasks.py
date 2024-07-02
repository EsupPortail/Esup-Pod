"""Esup-Pod encoding tasks."""

# pip3 install celery==5.4.0
# pip3 install webvtt-py
# pip3 install redis==4.5.4
from celery import Celery
import logging
import requests

# call local settings directly
# no need to load pod application to send statement
try:
    from ..custom import settings_local
except ImportError:
    from .. import settings as settings_local

EMAIL_HOST = getattr(settings_local, "EMAIL_HOST", "")
DEFAULT_FROM_EMAIL = getattr(settings_local, "DEFAULT_FROM_EMAIL", "")
ADMINS = getattr(settings_local, "ADMINS", ())
DEBUG = getattr(settings_local, "DEBUG", True)
TEST_REMOTE_ENCODE = getattr(settings_local, "TEST_REMOTE_ENCODE", False)

admins_email = [ad[1] for ad in ADMINS]

logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)

smtp_handler = logging.handlers.SMTPHandler(
    mailhost=EMAIL_HOST,
    fromaddr=DEFAULT_FROM_EMAIL,
    toaddrs=admins_email,
    subject="[POD ENCODING] Encoding Log Mail",
)
if not TEST_REMOTE_ENCODE:
    logger.addHandler(smtp_handler)

ENCODING_TRANSCODING_CELERY_BROKER_URL = getattr(
    settings_local, "ENCODING_TRANSCODING_CELERY_BROKER_URL", ""
)
POD_API_URL = getattr(settings_local, "POD_API_URL", "")
POD_API_TOKEN = getattr(settings_local, "POD_API_TOKEN", "")
encoding_app = Celery("encoding_tasks", broker=ENCODING_TRANSCODING_CELERY_BROKER_URL)
encoding_app.conf.task_routes = {
    "pod.video_encode_transcript.encoding_tasks.*": {"queue": "encoding"}
}


# celery -A pod.video_encode_transcript.encoding_tasks worker -l INFO -Q encoding
@encoding_app.task(bind=True)
def start_encoding_task(
    self, video_id, video_path, cut_start, cut_end, json_dressing, dressing_input
):
    """Start the encoding of the video."""
    print("Start the encoding of the video")
    from .Encoding_video import Encoding_video

    print(video_id, video_path, cut_start, cut_end)
    encoding_video = Encoding_video(
        video_id, video_path, cut_start, cut_end, json_dressing, dressing_input
    )
    encoding_video.start_encode()
    print("End of the encoding of the video")
    Headers = {"Authorization": "Token %s" % POD_API_TOKEN}
    url = POD_API_URL.strip("/") + "/store_remote_encoded_video/?id=%s" % video_id
    data = {
        "start": encoding_video.start,
        "video_id": video_id,
        "video_path": video_path,
        "cut_start": cut_start,
        "cut_end": cut_end,
        "stop": encoding_video.stop,
        "json_dressing": json_dressing,
        "dressing_input": dressing_input,
    }
    msg = "Task id : %s\n" % self.request.id
    try:
        response = requests.post(url, json=data, headers=Headers)
        if response.status_code != 200:
            msg += "Calling store remote encoding error: {} {}".format(
                response.status_code, response.reason
            )
            logger.error(msg + "\n" + str(response.content))
        else:
            logger.info(msg + "Call importing encoding task ok")
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.InvalidURL,
        requests.exceptions.Timeout,
    ) as exception:
        msg += "Exception: {}".format(type(exception).__name__)
        msg += "\nException message: {}".format(exception)
        logger.error(msg)


@encoding_app.task
def start_studio_task(recording_id, video_output, videos, subtime, presenter):
    from .encoding_studio import start_encode_video_studio

    print("Start the encoding studio of the video")
    msg = start_encode_video_studio(video_output, videos, subtime, presenter)
    print("End of the encoding studio of the video")
    Headers = {"Authorization": "Token %s" % POD_API_TOKEN}
    url = (
        POD_API_URL.strip("/")
        + "/store_remote_encoded_video_studio/?recording_id=%s" % recording_id
    )
    data = {
        "video_output": video_output,
        "msg": msg,
    }
    try:
        response = requests.post(url, json=data, headers=Headers)
        if response.status_code != 200:
            msg = "Calling store remote encoding studio error: {} {}".format(
                response.status_code, response.reason
            )
            logger.error(msg + "\n" + str(response.content))
        else:
            logger.info("Call importing encoded studio task ok")
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.ConnectionError,
        requests.exceptions.InvalidURL,
        requests.exceptions.Timeout,
    ) as exception:
        msg = "Exception: {}".format(type(exception).__name__)
        msg += "\nException message: {}".format(exception)
        logger.error(msg)
