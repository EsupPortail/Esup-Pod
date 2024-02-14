"""Long-standing operations"""

import logging
from urllib.parse import urlparse

import requests
from django.urls import reverse

from pod.activitypub.utils import ap_object
from pod.video.models import Video

from .constants import AP_DEFAULT_CONTEXT, AP_PT_VIDEO_CONTEXT, BASE_HEADERS
from .models import Follower, Following
from .serialization.video import ap_video_to_external_video, video_to_ap_video
from .utils import ap_post, ap_url

logger = logging.getLogger(__name__)


def index_videos(following: Following):
    ap_actor = get_instance_application_account_metadata(following.object)
    ap_outbox = ap_object(ap_actor["outbox"])
    if "first" in ap_outbox:
        index_videos_page(following, ap_outbox["first"])
    return True


def get_instance_application_account_url(url):
    """Read the instance nodeinfo well-known URL to get the main account URL."""
    # TODO: handle exceptions
    nodeinfo_url = f"{url}/.well-known/nodeinfo"
    response = requests.get(nodeinfo_url, headers=BASE_HEADERS)
    for link in response.json()["links"]:
        if link["rel"] == "https://www.w3.org/ns/activitystreams#Application":
            return link["href"]


def get_instance_application_account_metadata(domain):
    account_url = get_instance_application_account_url(domain)
    ap_actor = ap_object(account_url)
    return ap_actor


def handle_incoming_follow(ap_follow):
    # TODO: test double follows
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
    Follower.objects.filter(actor=ap_follow["actor"]).delete()


def send_follow_request(following: Following):
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


def index_videos_page(following: Following, page_url):
    """Parse a AP Video page payload, and handle each video."""
    ap_page = ap_object(page_url)
    for item in ap_page["orderedItems"]:
        index_video(following, item["object"])

    if "next" in ap_page:
        index_videos_page(following, ap_page["next"])


def index_video(following: Following, video_url):
    """Read a video payload and create an ExternalVideo object"""
    ap_video = ap_object(video_url)
    logger.warning(f"TODO: Deal with video indexation {ap_video}")
    extvideo = ap_video_to_external_video(ap_video)
    extvideo.source_instance = following
    extvideo.save()


def external_video_added_by_actor(ap_video, ap_actor):
    # Announce for a Video created by a user account
    # TODO: create an ExternalVideo
    logger.warning(f"TODO: Handle Video addition by {ap_actor['type']}")


def external_video_added_by_channel(ap_video, ap_channel):
    # Announce for a Video added to a channel
    # TODO: update the external video to add it to the matching channel
    logger.warning("TODO: Handle Video additon on Channel")


def external_video_update(ap_video):
    # TODO: update the external video details
    logger.warning("TODO: Deal with Video updates")


def external_video_deletion(ap_video):
    # TODO: Delete the ExternalVideo
    logger.warning("TODO: Handle Video deletion")


def send_video_announce_object(video: Video, follower: Follower):
    # TODO: save the inbox for better performance?
    actor_account = ap_object(follower.actor)
    inbox = actor_account["inbox"]

    video_ap_url = ap_url(reverse("activitypub:video", kwargs={"id": video.id}))
    owner_ap_url = ap_url(
        reverse("activitypub:account", kwargs={"username": video.owner.username})
    )

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


def send_video_update_object(video: Video, follower: Follower):
    # TODO: save the inbox for better performance?
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


def send_video_delete_object(video_id, owner_username, follower: Follower):
    # TODO: save the inbox for better performance?
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
    parsed = urlparse(ap_follow["object"])
    obj = f"{parsed.scheme}://{parsed.netloc}"
    follower = Following.objects.get(object=obj)
    follower.status = Following.Status.ACCEPTED
    follower.save()


def follow_request_rejected(ap_follow):
    parsed = urlparse(ap_follow["object"])
    obj = f"{parsed.scheme}://{parsed.netloc}"
    follower = Following.objects.get(object=obj)
    follower.status = Following.Status.REFUSED
    follower.save()
