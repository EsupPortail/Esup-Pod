from celery import Celery
from .. import settings
import logging

logger = logging.getLogger(__name__)

ENCODING_CELERY_BROKER_URL = getattr(settings, "ENCODING_CELERY_BROKER_URL", "")

importing_app = Celery(
    "importing_tasks",
    broker=ENCODING_CELERY_BROKER_URL
)
importing_app.conf.task_routes = {
    "pod.video_encode_transcript.importing_tasks.*": {"queue": "importing"}
}

# celery -A pod.video_encode_transcript.importing_tasks worker -l INFO -Q importing 
@importing_app.task
def start_importing_task(video_id, video_path):
    """Start the encoding of the video."""
    print("Start the importing of the video ID : %s" % video_id)
    from .Encoding_video_model import Encoding_video_model
    from django.conf import settings
    from .utils import (
        change_encoding_step,
        send_email_encoding,
    )
    from pod.video.models import Video
    EMAIL_ON_ENCODING_COMPLETION = getattr(settings, "EMAIL_ON_ENCODING_COMPLETION", True)
    encoding_video = Encoding_video_model(video_id, video_path)
    change_encoding_step(video_id, 3, "store encoding info")
    final_video = encoding_video.store_json_info()
    final_video.is_video = final_video.get_video_m4a() is None
    final_video.encoding_in_progress = False
    final_video.save()

    # envois mail fin encodage
    if EMAIL_ON_ENCODING_COMPLETION:
        video_to_encode = Video.objects.get(id=video_id)
        send_email_encoding(video_to_encode)

