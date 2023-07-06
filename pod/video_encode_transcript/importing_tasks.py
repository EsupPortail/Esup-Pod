from celery import Celery

try:
    from ..custom import settings_local
except ImportError:
    from .. import settings as settings_local
import logging

logger = logging.getLogger(__name__)

ENCODING_TRANSCODING_CELERY_BROKER_URL = getattr(
    settings_local, "ENCODING_TRANSCODING_CELERY_BROKER_URL", ""
)

importing_app = Celery("importing_tasks", broker=ENCODING_TRANSCODING_CELERY_BROKER_URL)
importing_app.conf.task_routes = {
    "pod.video_encode_transcript.importing_tasks.*": {"queue": "importing"}
}


# celery -A pod.video_encode_transcript.importing_tasks worker -l INFO -Q importing
@importing_app.task
def start_importing_task(start, video_id, video_path, cut_start, cut_end, stop):
    """Start the import of the encoding of the video."""
    print("Start the importing of the video: %s" % video_id)
    from .Encoding_video_model import Encoding_video_model
    from .encode import store_encoding_info, end_of_encoding

    encoding_video = Encoding_video_model(video_id, video_path, cut_start, cut_end)
    encoding_video.start = start
    encoding_video.stop = stop

    final_video = store_encoding_info(video_id, encoding_video)
    end_of_encoding(final_video)
