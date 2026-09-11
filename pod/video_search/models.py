"""Models for Esup-Pod video_search."""

from django.conf import settings
from pod.video_search.utils import index_es, delete_es
from pod.video.models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django.utils import translation

import threading

ES_URL = getattr(settings, "ES_URL", ["http://elasticsearch.localhost:9200/"])

# do it with contributor, overlay, chapter etc.


@receiver(post_save, sender=Video)
def update_video_index(
    sender, instance=None, created=False, **kwargs
) -> None:  # pragma: no cover
    """Index synchronously in tests, otherwise start a daemon thread."""
    if ES_URL is None:
        return
    # Use the test transaction's connection to avoid SQLite table locks.
    if getattr(settings, "TEST_SETTINGS", False):
        # Keep indexing's language changes local, as they are in a thread.
        with translation.override(settings.LANGUAGE_CODE):
            index_video(instance)
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
    """Delete synchronously in tests, otherwise start a daemon thread."""
    if ES_URL is None:
        return
    # Complete deletion before the next test can reuse the same video ID.
    if getattr(settings, "TEST_SETTINGS", False):
        delete_es(instance.id)
        return
    # delete_es(instance)
    t = threading.Thread(target=delete_es, args=[instance.id])
    t.daemon = True
    t.start()
