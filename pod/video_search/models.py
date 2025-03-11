"""Models for Esup-Pod video_search."""

from django.conf import settings
from pod.video_search.utils import index_es, delete_es
from pod.video.models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete

import threading

ES_URL = getattr(settings, "ES_URL", ["http://elasticsearch.localhost:9200/"])

# do it with contributor, overlay, chapter etc.


@receiver(post_save, sender=Video)
def update_video_index(
    sender, instance=None, created=False, **kwargs
) -> None:  # pragma: no cover
    """Start index_video as daemon thread."""
    if ES_URL is None:
        return
    t = threading.Thread(target=index_video, args=[instance])
    t.daemon = True
    t.start()


def index_video(video) -> None:  # pragma: no cover
    """Add video in ES index."""
    if video.is_draft is False and video.encoding_in_progress is False:
        index_es(video)
    else:
        delete_es(video.id)


@receiver(pre_delete, sender=Video)
def delete_video_index(
    sender, instance=None, created=False, **kwargs
) -> None:  # pragma: no cover
    """Start delete_es as daemon thread."""
    if ES_URL is None:
        return
    # delete_es(instance)
    t = threading.Thread(target=delete_es, args=[instance.id])
    t.daemon = True
    t.start()
