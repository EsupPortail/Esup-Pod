"""Signal callbacks."""

from django.db import transaction
from .tasks import (
    task_broadcast_local_video_creation,
    task_broadcast_local_video_deletion,
    task_broadcast_local_video_update,
)


def on_video_save(instance, created, **kwargs):
    """Celery tasks are triggered after commits and not just after .save() calls,
    so we are sure the database is really up to date at the moment we send data accross the network,
    and that any federated instance will be able to read the updated data.

    Without this, celery tasks could have been triggered BEFORE the data was actually written to the database,
    leading to old data being broadcasted.
    """

    def trigger_save_task():
        if created:
            task_broadcast_local_video_creation.delay(instance.id)

        else:
            task_broadcast_local_video_update.delay(instance.id)

    transaction.on_commit(trigger_save_task)


def on_video_delete(instance, **kwargs):
    """At the moment the celery task will be triggered,
    the video MAY already have been deleted.
    Thus, we avoid to pass a Video id to read in the database,
    and we directly pass pertinent data."""

    task_broadcast_local_video_deletion.delay(
        video_id=instance.id, owner_username=instance.owner.username
    )
