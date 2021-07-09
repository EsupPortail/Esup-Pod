from django.conf import settings
from pod.video_search.utils import index_es, delete_es
from pod.video.models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

import threading

TEST_SETTINGS = getattr(settings, "TEST_SETTINGS", False)
ES_URL = getattr(settings, "ES_URL", ["http://127.0.0.1:9200/"])

# do it  with contributor, overlay, chapter etc.


@receiver(post_save, sender=Video)
def update_video_index(
    sender, instance=None, created=False, **kwargs
):  # pragma: no cover
    if TEST_SETTINGS or ES_URL is None:
        return
    t = threading.Thread(target=index_video, args=[instance])
    t.setDaemon(True)
    t.start()


def index_video(video):  # pragma: no cover
    if video.is_draft is False and video.encoding_in_progress is False:
        index_es(video)
    else:
        delete_es(video)


@receiver(post_delete, sender=Video)
def delete_video_index(
    sender, instance=None, created=False, **kwargs
):  # pragma: no cover
    if TEST_SETTINGS or ES_URL is None:
        return
    # delete_es(instance)
    t = threading.Thread(target=delete_es, args=[instance])
    t.setDaemon(True)
    t.start()
