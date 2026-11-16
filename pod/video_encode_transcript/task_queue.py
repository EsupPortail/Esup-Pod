"""Queue ranking helpers for encoding/transcription task dispatch in Esup-Pod.

The queue is intentionally simple:
- only pending tasks receive a rank,
- rank is recomputed from scratch to keep ordering deterministic,
- non-pending tasks must not retain stale rank values.
"""

import logging
from typing import TypeAlias

from pod.video.models import Video

from .models import PriorityUser, Task

log = logging.getLogger(__name__)

QueuePriority: TypeAlias = int
HIGH_PRIORITY: QueuePriority = 0
NORMAL_PRIORITY: QueuePriority = 1
LOW_PRIORITY: QueuePriority = 2


def get_priority_user_ids() -> set[int]:
    """Return the set of users configured with absolute queue priority."""
    return set(PriorityUser.objects.values_list("user_id", flat=True))


def get_user_priority(
    video: Video,
    priority_user_ids: set[int] | None = None,
) -> QueuePriority:
    """Return queue priority for a video owner."""
    try:
        owner_id = getattr(video, "owner_id", None)
        if owner_id:
            if priority_user_ids is None:
                if PriorityUser.objects.filter(user_id=owner_id).exists():
                    return HIGH_PRIORITY
            elif owner_id in priority_user_ids:
                return HIGH_PRIORITY

        affiliation = video.owner.owner.affiliation
        if affiliation == "student":
            return LOW_PRIORITY
        return NORMAL_PRIORITY
    except AttributeError:
        log.warning(
            "Cannot determine affiliation for video %s owner. Defaulting to normal priority.",
            video.id,
        )
        return NORMAL_PRIORITY
    except Exception as exc:
        log.warning(
            "Error getting affiliation for video %s: %s. Defaulting to normal priority.",
            video.id,
            str(exc),
        )
        return NORMAL_PRIORITY


def _task_priority(
    task: Task,
    priority_user_ids: set[int] | None = None,
) -> QueuePriority:
    """Return priority for a pending task."""
    if not task.video_id or not task.video:
        return NORMAL_PRIORITY
    return get_user_priority(task.video, priority_user_ids=priority_user_ids)


def get_sorted_pending_tasks() -> list[Task]:
    """Return all pending tasks sorted by queue priority and creation date."""
    priority_user_ids = get_priority_user_ids()
    pending_tasks = list(
        Task.objects.filter(status="pending")
        .select_related("video", "video__owner", "video__owner__owner")
        .order_by("date_added", "id")
    )
    pending_tasks.sort(
        key=lambda task: (
            _task_priority(task, priority_user_ids=priority_user_ids),
            task.date_added,
            task.id,
        ),
    )
    return pending_tasks


def refresh_pending_task_ranks() -> None:
    """Recalculate rank for all pending tasks and clear rank for non-pending ones."""
    sorted_tasks = get_sorted_pending_tasks()
    updates: list[Task] = []
    for index, task in enumerate(sorted_tasks, start=1):
        if task.rank != index:
            task.rank = index
            updates.append(task)

    if updates:
        # Batch write only changed rows to avoid unnecessary UPDATE queries.
        Task.objects.bulk_update(updates, ["rank"])

    # Keep DB consistent: only pending tasks are expected to have a queue rank.
    Task.objects.exclude(status="pending").exclude(rank__isnull=True).update(rank=None)


def get_video_pending_encoding_queue_info(video: Video) -> tuple[int | None, int]:
    """Return (rank, total_pending) for the encoding task linked to a video."""
    queue_total = Task.objects.filter(status="pending").count()
    queue_task = (
        Task.objects.filter(video_id=video.id, type="encoding", status="pending")
        .order_by("date_added", "id")
        .first()
    )
    queue_rank = queue_task.rank if queue_task else None
    return queue_rank, queue_total
