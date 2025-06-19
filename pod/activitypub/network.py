"""Long-standing operations"""

import logging
from urllib.parse import urlparse

import requests
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from pod.activitypub.constants import (
    AP_DEFAULT_CONTEXT,
    AP_PT_VIDEO_CONTEXT,
    BASE_HEADERS,
)
from pod.activitypub.deserialization.video import (
    create_external_video,
    update_external_video,
    update_or_create_external_video,
)
from pod.activitypub.models import ExternalVideo, Follower, Following
from pod.activitypub.serialization.video import video_to_ap_video
from pod.activitypub.utils import ap_object, ap_post, ap_url
from pod.video.models import Video
from pod.video_search.utils import delete_es, index_es

logger = logging.getLogger(__name__)


def index_external_videos(following: Following):
    """Process activitypub video pages."""
    ap_actor = get_instance_application_account_metadata(following.object)
    ap_outbox = ap_object(ap_actor["outbox"])
    if "first" in ap_outbox:
        index_external_videos_page(following, ap_outbox["first"], [])
    return True


def get_instance_application_account_url(url):
    """Read the instance nodeinfo well-known URL to get the main account URL."""
    nodeinfo_url = f"{url}/.well-known/nodeinfo"
    response = requests.get(nodeinfo_url, headers=BASE_HEADERS)
    for link in response.json()["links"]:
        if link["rel"] == "https://www.w3.org/ns/activitystreams#Application":
            return link["href"]


def get_instance_application_account_metadata(domain):
    """Get activitypub actor data from domain."""
    account_url = get_instance_application_account_url(domain)
    ap_actor = ap_object(account_url)
    return ap_actor


def handle_incoming_follow(ap_follow):
    """Process activitypub follow activity."""
    actor_account = ap_object(ap_follow["actor"])
    inbox = actor_account["inbox"]

    follower, _ = Follower.objects.get_or_create(actor=ap_follow["actor"])
    payload = {
        "@context": AP_DEFAULT_CONTEXT,
        "id": ap_url(f"/accepts/follows/{follower.id}"),
        "type": "Accept",
        "actor": ap_follow["object"],
        "object": {
            "type": "Follow",
            "id": ap_follow["id"],
            "actor": ap_follow["actor"],
            "object": ap_follow["object"],
        },
    }
    response = ap_post(inbox, payload)
    return response.status_code == 204


def handle_incoming_unfollow(ap_follow):
    """Remove follower."""
    Follower.objects.filter(actor=ap_follow["actor"]).delete()


def send_follow_request(following: Following):
    """Send a follow request activity to another instance."""
    ap_actor = get_instance_application_account_metadata(following.object)
    following_url = ap_url(reverse("activitypub:following"))
    payload = {
        "@context": AP_DEFAULT_CONTEXT,
        "type": "Follow",
        "id": f"{following_url}/{following.id}",
        "actor": ap_url(reverse("activitypub:account")),
        "object": ap_actor["id"],
    }
    response = ap_post(ap_actor["inbox"], payload)
    following.status = Following.Status.REQUESTED
    following.save()

    return response.status_code == 204


def index_external_videos_page(
    following: Following, page_url, indexed_external_videos=[]
):
    """Parse a AP Video page payload, and handle each video."""
    ap_page = ap_object(page_url)
    for item in ap_page["orderedItems"]:
        indexed_external_videos.append(index_external_video(following, item["object"]))

    if "next" in ap_page:
        index_external_videos_page(following, ap_page["next"], indexed_external_videos)
    ExternalVideo.objects.filter(source_instance=following).exclude(
        ap_id__in=indexed_external_videos
    ).delete()


def index_external_video(following: Following, video_url):
    """Read a video payload and create an ExternalVideo object."""
    ap_video = ap_object(video_url)
    external_video = update_or_create_external_video(
        payload=ap_video, source_instance=following
    )
    index_es(media=external_video)
    return external_video.ap_id


def external_video_added_by_actor(ap_video, ap_actor):
    """Process video creation from actor activity."""
    logger.info(
        "ActivityPub task call ExternalVideo %s creation from actor %s",
        ap_video,
        ap_actor,
    )
    try:
        plausible_following = get_related_following(ap_actor=ap_actor["id"])
        existing_e_video = get_external_video_with_related_following(
            ap_video_id=ap_video["id"], plausible_following=plausible_following
        )
        logger.warning(
            "Received an ActivityPub create activity from actor %s on an already existing ExternalVideo %s",
            ap_actor["id"],
            existing_e_video.id,
        )
    except Following.DoesNotExist:
        logger.warning(
            "Received an ActivityPub create activity from unknown actor %s",
            ap_actor["id"],
        )
    except PermissionDenied:
        logger.warning(
            "Actor %s cannot execute ActivityPub actions", plausible_following.object
        )
    except ExternalVideo.DoesNotExist:
        external_video = create_external_video(
            payload=ap_video, source_instance=plausible_following
        )
        index_es(media=external_video)


def external_video_added_by_channel(ap_video, ap_channel):
    """Process video creation activity from channel."""
    logger.info(
        "ActivityPub task call ExternalVideo %s creation from channel %s",
        ap_video,
        ap_channel,
    )
    try:
        plausible_following = get_related_following(ap_actor=ap_channel["id"])
        existing_e_video = get_external_video_with_related_following(
            ap_video_id=ap_video["id"], plausible_following=plausible_following
        )
        logger.warning(
            "Received an ActivityPub create activity from channel %s on an already existing ExternalVideo %s",
            ap_channel["id"],
            existing_e_video.id,
        )
    except Following.DoesNotExist:
        logger.warning(
            "Received an ActivityPub create activity from unknown channel %s",
            ap_channel["id"],
        )
    except PermissionDenied:
        logger.warning(
            "Actor %s cannot execute ActivityPub actions", plausible_following.object
        )
    except ExternalVideo.DoesNotExist:
        external_video = create_external_video(
            payload=ap_video, source_instance=plausible_following
        )
        index_es(media=external_video)


def external_video_update(ap_video, ap_actor):
    """Process video update activity."""
    logger.info("ActivityPub task call ExternalVideo %s update", ap_video["id"])
    try:
        plausible_following = get_related_following(ap_actor=ap_actor)
        e_video_to_update = get_external_video_with_related_following(
            ap_video_id=ap_video["id"], plausible_following=plausible_following
        )
        external_video = update_external_video(
            external_video=e_video_to_update,
            payload=ap_video,
            source_instance=plausible_following,
        )
        index_es(media=external_video)
    except Following.DoesNotExist:
        logger.warning(
            "Received an ActivityPub update activity from unknown actor %s", ap_actor
        )
    except PermissionDenied:
        logger.warning(
            "Actor %s cannot execute ActivityPub actions", plausible_following.object
        )
    except ExternalVideo.DoesNotExist:
        logger.warning(
            "Received an ActivityPub update activity on a nonexistent ExternalVideo %s",
            ap_video["id"],
        )


def external_video_deletion(ap_video_id, ap_actor):
    """Process video delete activity."""
    logger.info("ActivityPub task call ExternalVideo %s delete", ap_video_id)
    try:
        plausible_following = get_related_following(ap_actor=ap_actor)
        external_video_to_delete = get_external_video_with_related_following(
            ap_video_id=ap_video_id, plausible_following=plausible_following
        )
        delete_es(media=external_video_to_delete)
        external_video_to_delete.delete()
    except Following.DoesNotExist:
        logger.warning(
            "Received an ActivityPub delete activity from unknown actor %s", ap_actor
        )
    except PermissionDenied:
        logger.warning(
            "Actor %s cannot execute ActivityPub actions", plausible_following.object
        )
    except ExternalVideo.DoesNotExist:
        logger.warning(
            "Received an ActivityPub delete activity on a nonexistent ExternalVideo %s from actor %s",
            ap_video_id,
            plausible_following.object,
        )


def get_related_following(ap_actor):
    """Check actor is indeed followed."""
    actor_domain = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(ap_actor))
    actor = Following.objects.get(object__startswith=actor_domain)
    return actor


def get_external_video_with_related_following(ap_video_id, plausible_following):
    """Check actor has accepted follow and is owner of external video."""
    if not plausible_following.status == Following.Status.ACCEPTED:
        raise PermissionDenied
    external_video = ExternalVideo.objects.get(
        ap_id=ap_video_id, source_instance=plausible_following
    )
    return external_video


def send_video_create_activity(video: Video, follower: Follower):
    """Unicast a video Create activity."""
    actor_account = ap_object(follower.actor)
    inbox = actor_account["inbox"]

    owner_ap_url = ap_url(
        reverse("activitypub:account", kwargs={"username": video.owner.username})
    )
    video_ap_url = ap_url(reverse("activitypub:video", kwargs={"id": video.id}))
    payload = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
            {"RsaSignature2017": "https://w3id.org/security#RsaSignature2017"},
        ],
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            ap_url(reverse("activitypub:followers")),
            ap_url(
                reverse(
                    "activitypub:followers", kwargs={"username": video.owner.username}
                )
            ),
        ],
        "cc": [],
        "type": "Create",
        "id": f"{video_ap_url}/create",
        "actor": owner_ap_url,
        "object": video_ap_url,
    }
    response = ap_post(inbox, payload)
    return response.status_code == 204


def send_video_announce_activity(video: Video, follower: Follower, owner_ap_url):
    """Unicast a video Announce activity."""
    actor_account = ap_object(follower.actor)
    inbox = actor_account["inbox"]

    video_ap_url = ap_url(reverse("activitypub:video", kwargs={"id": video.id}))
    payload = {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/v1",
            {"RsaSignature2017": "https://w3id.org/security#RsaSignature2017"},
        ],
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            ap_url(reverse("activitypub:followers")),
            ap_url(
                reverse(
                    "activitypub:followers", kwargs={"username": video.owner.username}
                )
            ),
        ],
        "cc": [],
        "type": "Announce",
        "id": f"{video_ap_url}/announces/1",
        "actor": owner_ap_url,
        "object": video_ap_url,
    }
    response = ap_post(inbox, payload)
    return response.status_code == 204


def send_video_creation_activities(video: Video, follower: Follower):
    """Unicast several activities related to the video creation:
    - A Create activity emitted by the video owner
    - An Announce activity emitted from the pod meta account
    - An Announce activity emitted from the video owner channel.
    """
    meta_account_ap_url = ap_url(reverse("activitypub:account"))
    group_account_ap_url = ap_url(
        reverse(
            "activitypub:account_channel", kwargs={"username": video.owner.username}
        )
    )

    send_video_create_activity(video, follower)
    send_video_announce_activity(video, follower, meta_account_ap_url)
    send_video_announce_activity(video, follower, group_account_ap_url)


def send_video_update_activity(video: Video, follower: Follower):
    """Unicast a video update announce."""
    actor_account = ap_object(follower.actor)
    inbox = actor_account["inbox"]

    video_ap_url = ap_url(reverse("activitypub:video", kwargs={"id": video.id}))
    owner_ap_url = ap_url(
        reverse("activitypub:account", kwargs={"username": video.owner.username})
    )

    payload = {
        "@context": AP_DEFAULT_CONTEXT + [AP_PT_VIDEO_CONTEXT],
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "cc": [
            ap_url(reverse("activitypub:followers")),
            ap_url(
                reverse(
                    "activitypub:followers", kwargs={"username": video.owner.username}
                )
            ),
        ],
        "type": "Update",
        "id": video_ap_url,
        "actor": owner_ap_url,
        "object": {
            **video_to_ap_video(video),
        },
    }
    response = ap_post(inbox, payload)
    return response.status_code == 204


def send_video_delete_activity(video_id, owner_username, follower: Follower):
    """Unicast a video delete object."""
    actor_account = ap_object(follower.actor)
    inbox = actor_account["inbox"]

    video_ap_url = ap_url(reverse("activitypub:video", kwargs={"id": video_id}))
    owner_ap_url = ap_url(
        reverse("activitypub:account", kwargs={"username": owner_username})
    )
    payload = {
        "@context": AP_DEFAULT_CONTEXT,
        "to": [
            "https://www.w3.org/ns/activitystreams#Public",
            ap_url(reverse("activitypub:followers")),
            ap_url(
                reverse("activitypub:followers", kwargs={"username": owner_username})
            ),
        ],
        "cc": [],
        "type": "Delete",
        "id": f"{video_ap_url}/delete",
        "actor": owner_ap_url,
        "object": video_ap_url,
    }

    response = ap_post(inbox, payload)
    return response.status_code == 204


def follow_request_accepted(ap_follow):
    """Process follow request acceptation."""
    parsed = urlparse(ap_follow["object"])
    obj = f"{parsed.scheme}://{parsed.netloc}"
    follower = Following.objects.get(object=obj)
    follower.status = Following.Status.ACCEPTED
    follower.save()


def follow_request_rejected(ap_follow):
    """Process follow request rejection."""
    parsed = urlparse(ap_follow["object"])
    obj = f"{parsed.scheme}://{parsed.netloc}"
    follower = Following.objects.get(object=obj)
    follower.status = Following.Status.REFUSED
    follower.save()
