# pip3 install celery==5.2.7
# pip3 install webvtt-py
# pip3 install redis==4.5.4
from celery import Celery
from tempfile import NamedTemporaryFile
import logging
import os
# call local settings directly
# no need to load pod application to send statement
try:
    from ..custom import settings_local
except ImportError:
    from .. import settings as settings_local

logger = logging.getLogger(__name__)

ENCODING_TRANSCODING_CELERY_BROKER_URL = getattr(
    settings_local,
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
transcripting_app.autodiscover_tasks(packages=None, related_name='', force=False)


# celery \
# -A pod.video_encode_transcript.transcripting_tasks worker \
# -l INFO -Q transcripting
@transcripting_app.task
def start_transcripting_task(video_id, mp3filepath, duration, lang):
    """Start the transcripting of the video."""
    from .transcript_model import start_transcripting
    from .importing_transcript_tasks import start_importing_transcript_task
    from ..main.settings import MEDIA_ROOT
    print("Start the transcripting of the video %s" % video_id)
    print(video_id, mp3filepath, duration, lang)
    msg, text_webvtt = start_transcripting(mp3filepath, duration, lang)
    print("End of the transcripting of the video")
    media_temp_dir = os.path.join(MEDIA_ROOT, "temp")
    if not os.path.exists(media_temp_dir):
        os.mkdir(media_temp_dir)
    temp_vtt_file = NamedTemporaryFile(
        dir=media_temp_dir,
        delete=False,
        suffix=".vtt"
    )
    text_webvtt.save(temp_vtt_file.name)
    start_importing_transcript_task.delay(video_id, msg, temp_vtt_file.name)
