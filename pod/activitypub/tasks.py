"""Celery tasks configuration."""

from django.conf import settings

try:
    from ..custom import settings_local
except ImportError:
    from .. import settings as settings_local

from celery import Celery
from celery.utils.log import get_task_logger

ACTIVITYPUB_CELERY_BROKER_URL = getattr(
    settings_local, "ACTIVITYPUB_CELERY_BROKER_URL", ""
)
CELERY_TASK_ALWAYS_EAGER = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)

activitypub_app = Celery("activitypub", broker=ACTIVITYPUB_CELERY_BROKER_URL)
activitypub_app.conf.task_routes = {"pod.activitypub.tasks.*": {"queue": "activitypub"}}
activitypub_app.conf.task_always_eager = CELERY_TASK_ALWAYS_EAGER
activitypub_app.conf.task_eager_propagates = CELERY_TASK_ALWAYS_EAGER

logger = get_task_logger(__name__)


@activitypub_app.task()
def task_follow(following_id):
    from .models import Following
    from .network import send_follow_request

    following = Following.objects.get(id=following_id)
    return send_follow_request(following)


@activitypub_app.task()
def task_index_videos(following_id):
    from .models import Following
    from .network import index_videos

    following = Following.objects.get(id=following_id)
    return index_videos(following)


@activitypub_app.task()
def task_handle_inbox_follow(username, data):
    from .network import handle_incoming_follow

    return handle_incoming_follow(ap_follow=data)


@activitypub_app.task()
def task_handle_inbox_accept(username, data):
    from pod.activitypub.utils import ap_object

    from .network import follow_request_accepted

    obj = ap_object(data["object"])
    if obj["type"] == "Follow":
        return follow_request_accepted(ap_follow=data["object"])

    logger.debug("Ignoring inbox 'Accept' action for '%s' object", obj["type"])


@activitypub_app.task()
def task_handle_inbox_reject(username, data):
    from pod.activitypub.utils import ap_object

    from .network import follow_request_rejected

    obj = ap_object(data["object"])
    if obj["type"] == "Follow":
        return follow_request_rejected(ap_follow=data["object"])

    logger.debug("Ignoring inbox 'Reject' action for '%s' object", obj["type"])


@activitypub_app.task()
def task_handle_inbox_announce(username, data):
    from pod.activitypub.utils import ap_object

    from .network import external_video_added_by_actor, external_video_added_by_channel

    obj = ap_object(data["object"])
    actor = ap_object(data["actor"])

    if obj["type"] == "Video":
        if actor["type"] in ("Application", "Person"):
            return external_video_added_by_actor(ap_video=obj, ap_actor=actor)

        elif actor["type"] in ("Group",):
            return external_video_added_by_channel(ap_video=obj, ap_channel=actor)

    logger.debug("Ignoring inbox 'Announce' action for '%s' object", obj["type"])


@activitypub_app.task()
def task_handle_inbox_update(username, data):
    from pod.activitypub.utils import ap_object

    from .network import external_video_update

    obj = ap_object(data["object"])
    if obj["type"] == "Video":
        return external_video_update(ap_video=obj)

    logger.debug("Ignoring inbox 'Update' action for '%s' object", obj["type"])


@activitypub_app.task()
def task_handle_inbox_delete(username, data):
    from pod.activitypub.utils import ap_object

    from .network import external_video_deletion

    obj = ap_object(data["object"])
    if obj["type"] == "Video":
        return external_video_deletion(ap_video=obj)

    logger.debug("Ignoring inbox 'Delete' action for '%s' object", obj["type"])


@activitypub_app.task()
def task_handle_inbox_undo(username, data):
    from pod.activitypub.utils import ap_object

    from .network import handle_incoming_unfollow

    obj = ap_object(data["object"])
    if obj["type"] == "Follow":
        return handle_incoming_unfollow(ap_follow=obj)

    logger.debug("Ignoring inbox 'Undo' action for '%s' object", obj["type"])


@activitypub_app.task()
def task_broadcast_local_video_creation(video_id):
    from pod.video.models import Video

    from .models import Follower
    from .network import send_video_announce_object

    video = Video.objects.get(id=video_id)
    # TODO: maybe delegate in subtasks for better performance?
    for follower in Follower.objects.all():
        send_video_announce_object(video, follower)


@activitypub_app.task()
def task_broadcast_local_video_update(video_id):
    from pod.video.models import Video

    from .models import Follower
    from .network import send_video_update_object

    video = Video.objects.get(id=video_id)
    # TODO: maybe delegate in subtasks for better performance?
    for follower in Follower.objects.all():
        send_video_update_object(video, follower)


@activitypub_app.task()
def task_broadcast_local_video_deletion(video_id, owner_username):
    from .models import Follower
    from .network import send_video_delete_object

    # TODO: maybe delegate in subtasks for better performance?
    for follower in Follower.objects.all():
        send_video_delete_object(video_id, owner_username, follower)
