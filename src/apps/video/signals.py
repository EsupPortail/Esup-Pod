"""
Esup-Pod - Video application signals.
"""

import logging
import os

from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from src.apps.video.models import Video, Type, Subtitle
from src.apps.video.services.metadata import extract_video_duration
from src.apps.utils.files import safe_remove_file

logger = logging.getLogger(__name__)

# Cache keys to invalidate when a video changes (same logic as V4 cache.delete_many)
_VIDEO_CACHE_KEYS = ["pod:video:metadata"]


def _invalidate_video_caches():
    """
    Invalidates all application caches related to video data.
    V4 equivalent: cache.delete_many(["DISCIPLINES", "VIDEOS_COUNT", ...])
    + pattern-based deletion of all search caches.
    """
    cache.delete_many(_VIDEO_CACHE_KEYS)
    logger.debug("Cache invalidated: %s", _VIDEO_CACHE_KEYS)

    # Pattern-based search cache invalidation (requires django-redis)
    try:
        cache.delete_pattern("pod:search:*")
        logger.debug("Cache invalidated: pod:search:*")
    except AttributeError:
        # If the backend is not django-redis (e.g., locmem in test), fail silently
        logger.debug("delete_pattern not supported on current cache backend — ignored")


@receiver(post_save, sender=Video)
def set_video_slug(sender, instance, created, **kwargs):
    """
    Generates the V4-compatible slug after the first INSERT.

    Format: "%04d-<slugified-title>" (e.g. "0042-video-title")

    NOTE: unlike V4 which recomputed the slug on every save(),
    V5 intentionally freezes the slug at creation time.
    If the title changes, the slug (and therefore the permalink) does not change.
    """
    if created and not instance.slug:
        id_padded = "%04d" % instance.pk
        new_slug = f"{id_padded}-{slugify(instance.title)}"
        Video.objects.filter(pk=instance.pk).update(slug=new_slug)
        instance.slug = new_slug


@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes physical files from the disk when the Video object is deleted.
    """
    from src.apps.video.conf import video_settings

    if video_settings.delete_source_on_video_delete:
        safe_remove_file(instance.video_file)

    safe_remove_file(instance.thumbnail)
    safe_remove_file(instance.overview)


@receiver(post_delete, sender=Subtitle)
def auto_delete_subtitle_file_on_delete(sender, instance, **kwargs):
    """
    Deletes physical subtitle files from disk when Subtitle object is deleted.
    """
    safe_remove_file(instance.file)


@receiver(pre_save, sender=Video)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes the old file if a new version is uploaded for the same video.
    """
    if not instance.pk:
        return False

    try:
        old_file = Video.objects.get(pk=instance.pk).video_file
    except Video.DoesNotExist:
        return False

    new_file = instance.video_file
    if old_file and not old_file == new_file:
        safe_remove_file(old_file)


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    At the time of creation (upload finished), calculate the duration.
    """
    logger.debug(
        "video_post_save triggered. created=%s, file=%s",
        created,
        instance.video_file,
    )
    if created and instance.video_file:
        if instance.duration == 0:
            file_path = instance.video_file.path
            logger.debug(
                "Processing file at %s. exists=%s",
                file_path,
                os.path.exists(file_path),
            )
            if os.path.exists(file_path):
                duration = extract_video_duration(file_path)
                logger.debug(
                    "Extracted duration=%s. Updating status to PUBLISHED...", duration
                )
                Video.objects.filter(pk=instance.pk).update(duration=duration)
                logger.info(
                    "Video pk=%s published with duration=%ss.", instance.pk, duration
                )


@receiver(post_save, sender=Video)
def auto_assign_site_to_video(sender, instance, created, **kwargs):
    """
    Fallback signal: Ensures the video is linked to the current site
    if created via admin or other means.
    """
    if created:
        try:
            current_site = Site.objects.get_current()
            if not instance.sites.filter(pk=current_site.pk).exists():
                instance.sites.add(current_site)
        except Exception as e:
            logger.warning("Could not auto-assign site to video %s: %s", instance.pk, e)


@receiver(post_save, sender=Type)
def auto_assign_site_to_type(sender, instance, created, **kwargs):
    """
    Fallback signal: Ensures the type is linked to the current site
    if created via admin or other means.
    """
    if created:
        try:
            current_site = Site.objects.get_current()
            if not instance.sites.filter(pk=current_site.pk).exists():
                instance.sites.add(current_site)
        except Exception as e:
            logger.warning("Could not auto-assign site to type %s: %s", instance.pk, e)


@receiver(post_save, sender=Video)
def invalidate_cache_on_video_save(sender, instance, **kwargs):
    """
    Invalidates application caches after any video update.
    V4 equivalent: the `cache_video_data` command was called by cron
    — here we invalidate directly upon change.
    """
    _invalidate_video_caches()


@receiver(post_delete, sender=Video)
def invalidate_cache_on_video_delete(sender, instance, **kwargs):
    """
    Invalidates application caches after a video is deleted.
    """
    _invalidate_video_caches()
