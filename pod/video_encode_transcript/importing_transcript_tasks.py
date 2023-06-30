from celery import Celery
from .. import settings
import logging
logger = logging.getLogger(__name__)

ENCODING_TRANSCODING_CELERY_BROKER_URL = getattr(
    settings,
    "ENCODING_TRANSCODING_CELERY_BROKER_URL",
    ""
)

importing_transcript_app = Celery(
    "importing_transcript_tasks",
    broker=ENCODING_TRANSCODING_CELERY_BROKER_URL
)
importing_transcript_app.conf.task_routes = {
    "pod.video_encode_transcript.importing_transcript_tasks.*": {
        "queue": "importing_transcript"
    }
}


# celery -A pod.video_encode_transcript.importing_tasks worker -l INFO -Q importing
@importing_transcript_app.task
def start_importing_transcript_task(video_id, msg, webvtt):
    """Start the encoding of the video."""
    print("Start the importing transcript of the video ID : %s" % video_id)
    from pod.video.models import Video
    from .transcript import save_vtt_and_notify
    video_to_encode = Video.objects.get(id=video_id)
    save_vtt_and_notify(video_to_encode, msg, webvtt)
