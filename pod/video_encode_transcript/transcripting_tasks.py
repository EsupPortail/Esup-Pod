# pip3 install celery==5.2.7
# pip3 install webvtt-py
# pip3 install redis==4.5.4
from celery import Celery
import logging
# call local settings directly
# no need to load pod application to send statement
from .. import settings

logger = logging.getLogger(__name__)

ENCODING_TRANSCODING_CELERY_BROKER_URL = getattr(
    settings,
    "ENCODING_TRANSCODING_CELERY_BROKER_URL",
    ""
)

transcripting_app = Celery(
    "transcripting_tasks",
    broker=ENCODING_TRANSCODING_CELERY_BROKER_URL
)
transcripting_app.conf.task_routes = {
    "pod.video_encode_transcript.transcripting_tasks.*": {"queue": "transcripting"}
}


# celery \
# -A pod.video_encode_transcript.transcripting_tasks worker \
# -l INFO -Q transcripting
@transcripting_app.task
def start_transcripting_task(video_id, mp3filepath, duration, lang):
    """Start the encoding of the video."""
    from .transcript_model import start_transcripting
    from .importing_transcript_tasks import start_importing_transcript_task
    print("Start the transcripting of the video %s" % video_id)
    msg, webvtt = start_transcripting(mp3filepath, duration, lang)
    print("End of the transcripting of the video")
    start_importing_transcript_task.delay(video_id, msg, str(webvtt))
