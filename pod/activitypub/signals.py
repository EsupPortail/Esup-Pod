"""Signal callbacks."""

import logging
from django.db import transaction
from .tasks import (
    task_broadcast_local_video_creation,
    task_broadcast_local_video_deletion,
    task_broadcast_local_video_update,
)

logger = logging.getLogger(__name__)


def on_video_pre_save(instance, sender, **kwargs):
    """Create temporary attribute to compare previous state after video save."""
    instance._was_activity_pub_broadcasted = instance.is_activity_pub_broadcasted
    instance.is_activity_pub_broadcasted = instance.is_visible()


def on_video_save(instance, sender, **kwargs):
    """Celery tasks are triggered after commits and not just after .save() calls,
    so we are sure the database is really up to date at the moment we send data accross the network,
    and that any federated instance will be able to read the updated data.

    Without this, celery tasks could have been triggered BEFORE the data was actually written to the database,
    leading to old data being broadcasted.
    """

    def trigger_save_task():
        if (
            not instance._was_activity_pub_broadcasted
            and instance.is_activity_pub_broadcasted
        ):
            logger.info(
                "Save publicly visible %s and broadcast a creation ActivityPub task",
                instance,
            )
            task_broadcast_local_video_creation.delay(instance.id)

        elif (
            instance._was_activity_pub_broadcasted
            and not instance.is_activity_pub_broadcasted
        ):
            logger.info(
                "Save publicly invisible %s and broadcast a deletion ActivityPub task",
                instance,
            )
            task_broadcast_local_video_deletion.delay(
                video_id=instance.id, owner_username=instance.owner.username
            )
        elif (
            instance._was_activity_pub_broadcasted
            and instance.is_activity_pub_broadcasted
        ):
            logger.info(
                "Save publicly visible %s and broadcast an update ActivityPub task",
                instance,
            )
            task_broadcast_local_video_update.delay(instance.id)

        del instance._was_activity_pub_broadcasted

    transaction.on_commit(trigger_save_task)


def on_video_delete(instance, **kwargs):
    """At the moment the celery task will be triggered,
    the video MAY already have been deleted.
    Thus, we avoid to pass a Video id to read in the database,
    and we directly pass pertinent data."""

    task_broadcast_local_video_deletion.delay(
        video_id=instance.id, owner_username=instance.owner.username
    )
