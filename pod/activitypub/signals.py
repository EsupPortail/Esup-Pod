"""Signal callbacks."""

import logging
from django.db import transaction
from .tasks import (
    task_broadcast_local_video_creation,
    task_broadcast_local_video_deletion,
    task_broadcast_local_video_update,
)

logger = logging.getLogger(__name__)


def is_new_and_visible(current_state, previous_state):
    return (
        not previous_state
        and current_state
        and not current_state.is_draft
        and current_state.encoded
        and not current_state.encoding_in_progress
        and not current_state.is_restricted
        and not current_state.password
    )


def has_changed_to_visible(current_state, previous_state):
    return (
        previous_state
        and current_state
        and (
            (
                previous_state.is_draft
                and not current_state.is_draft
                and current_state.encoded
                and not current_state.encoding_in_progress
                and not current_state.is_restricted
                and not current_state.password
            )
            or (
                previous_state.encoding_in_progress
                and not current_state.is_draft
                and current_state.encoded
                and not current_state.encoding_in_progress
                and not current_state.is_restricted
                and not current_state.password
            )
            or (
                previous_state.is_restricted
                and not current_state.is_draft
                and current_state.encoded
                and not current_state.encoding_in_progress
                and not current_state.is_restricted
                and not current_state.password
            )
            or (
                previous_state.password
                and not current_state.is_draft
                and current_state.encoded
                and not current_state.encoding_in_progress
                and not current_state.is_restricted
                and not current_state.password
            )
        )
    )


def has_changed_to_invisible(current_state, previous_state):
    return (
        previous_state
        and current_state
        and (
            (not previous_state.is_draft and current_state.is_draft)
            or (not previous_state.is_restricted and current_state.is_restricted)
            or (not previous_state.password and current_state.password)
        )
    )


def is_still_visible(current_state, previous_state):
    return (
        previous_state
        and current_state
        and not previous_state.is_draft
        and not current_state.is_draft
        and previous_state.encoded
        and not previous_state.encoding_in_progress
        and current_state.encoded
        and not current_state.encoding_in_progress
        and not previous_state.is_restricted
        and not current_state.is_restricted
        and not previous_state.password
        and not current_state.password
    )


def on_video_pre_save(instance, sender, **kwargs):
    try:
        instance._pre_save_instance = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        instance._pre_save_instance = None


def on_video_save(instance, sender, **kwargs):
    """Celery tasks are triggered after commits and not just after .save() calls,
    so we are sure the database is really up to date at the moment we send data accross the network,
    and that any federated instance will be able to read the updated data.

    Without this, celery tasks could have been triggered BEFORE the data was actually written to the database,
    leading to old data being broadcasted.
    """

    def trigger_save_task():
        previous_state = instance._pre_save_instance

        if is_new_and_visible(
            current_state=instance, previous_state=previous_state
        ) or has_changed_to_visible(
            current_state=instance, previous_state=previous_state
        ):
            logger.info(
                "Save publicly visible %s and broadcast a creation ActivityPub task",
                instance,
            )
            task_broadcast_local_video_creation.delay(instance.id)

        elif has_changed_to_invisible(
            current_state=instance, previous_state=previous_state
        ):
            logger.info(
                "Save publicly invisible %s and broadcast a deletion ActivityPub task",
                instance,
            )
            task_broadcast_local_video_deletion.delay(
                video_id=instance.id, owner_username=instance.owner.username
            )
        elif is_still_visible(current_state=instance, previous_state=previous_state):
            logger.info(
                "Save publicly visible %s and broadcast an update ActivityPub task",
                instance,
            )
            task_broadcast_local_video_update.delay(instance.id)

        del instance._pre_save_instance

    transaction.on_commit(trigger_save_task)


def on_video_delete(instance, **kwargs):
    """At the moment the celery task will be triggered,
    the video MAY already have been deleted.
    Thus, we avoid to pass a Video id to read in the database,
    and we directly pass pertinent data."""

    task_broadcast_local_video_deletion.delay(
        video_id=instance.id, owner_username=instance.owner.username
    )
