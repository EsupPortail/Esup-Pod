"""
Esup-Pod - Search application signals.

Connects post_save / pre_delete signals on Video to keep the
Redis Search index in sync automatically (like V4 behaviour).

Controlled by: SEARCH_ENABLE_AUTO_INDEX (default: True).
"""

import logging
import threading

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _index_video_async(video_id: int) -> None:
    """Re-index a single video in Redis Search in a background daemon thread."""
    from src.apps.search.services.indexer import index_video_by_id

    try:
        index_video_by_id(video_id)
    except Exception as exc:
        logger.warning("Auto-index failed for video pk=%s: %s", video_id, exc)


def _delete_video_async(video_id: int) -> None:
    """Remove a single video from the Redis Search index in a daemon thread."""
    from src.apps.search.services.indexer import delete_video_from_index

    try:
        delete_video_from_index(video_id)
    except Exception as exc:
        logger.warning("Auto-delete from index failed for video pk=%s: %s", video_id, exc)


def _connect_signals():
    """
    Connect post_save / pre_delete signals on Video.
    Called lazily (inside ready()) to avoid circular imports.
    """
    from src.apps.video.models import Video
    from src.apps.search.conf import search_settings

    if not search_settings.search_enable_auto_index or search_settings.is_disabled:
        logger.debug(
            "Search auto-indexing is disabled (SEARCH_ENABLE_AUTO_INDEX=False "
            "or SEARCH_ENGINE=disabled). Skipping signal registration."
        )
        return

    @receiver(post_save, sender=Video, weak=False)
    def video_post_save_search(sender, instance, **kwargs):
        """
        Re-index the video after any save.

        Only indexes PUBLISHED or RESTRICTED videos (not drafts).
        Runs in a daemon thread to avoid blocking the request/response cycle,
        exactly like V4's update_video_index().
        """
        from src.apps.search.conf import search_settings as _ss

        if not _ss.is_redis:
            return

        if instance.status == instance.Status.DRAFT:
            # Draft → remove from index (same logic as V4: is_draft=True → delete_es)
            t = threading.Thread(target=_delete_video_async, args=[instance.pk])
            t.daemon = True
            t.start()
        else:
            t = threading.Thread(target=_index_video_async, args=[instance.pk])
            t.daemon = True
            t.start()

    @receiver(pre_delete, sender=Video, weak=False)
    def video_pre_delete_search(sender, instance, **kwargs):
        """Remove the video from the Redis Search index before deletion."""
        from src.apps.search.conf import search_settings as _ss

        if not _ss.is_redis:
            return

        t = threading.Thread(target=_delete_video_async, args=[instance.pk])
        t.daemon = True
        t.start()

    logger.debug("Search auto-index signals connected for Video model.")


_connect_signals()
