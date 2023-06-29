# xapi/tasks.py
from celery import Celery
import requests
import logging
from requests.auth import HTTPBasicAuth

# call local settings directly
# no need to load pod application to send statement
from .. import settings

logger = logging.getLogger(__name__)

ENCODING_CELERY_BROKER_URL = getattr(settings, "ENCODING_CELERY_BROKER_URL", "")

encoding_app = Celery("encoding_tasks", broker=ENCODING_CELERY_BROKER_URL)
encoding_app.conf.task_routes = {"pod.video_encode_transcript.encoding_tasks.*": {"queue": "encoding"}}


@encoding_app.task
def start_encoding_task(video_id):
    """Start the encoding of the video."""
    print("Start the encoding of the video")
    x = requests.post(
        XAPI_LRS_URL, json=statement, auth=HTTPBasicAuth(XAPI_LRS_LOGIN, XAPI_LRS_PWD)
    )
    if x.status_code == 200:
        print(x.text)
        logger.info("statement id: %s" % x.text)
    else:
        logger.error("Error during sending statement: %s" % x.text)
