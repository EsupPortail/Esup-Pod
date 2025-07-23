from django.conf import settings
from django.urls import reverse

from pod.activitypub.utils import ap_url


def channel_to_ap_group(channel):
    """Serialize channel to activitypub group."""
    return {
        "type": "Group",
        "id": ap_url(reverse("activitypub:channel", kwargs={"id": channel.id})),
        **channel_url(channel),
        **channel_following(channel),
        **channel_followers(channel),
        **channel_playlists(channel),
        **channel_outbox(channel),
        **channel_inbox(channel),
        **channel_preferred_username(channel),
        **channel_name(channel),
        **channel_endpoints(channel),
        **channel_public_key(channel),
        **channel_published(channel),
        **channel_icon(channel),
        **channel_support(channel),
        **channel_attributed_to(channel),
        **channel_image(channel),
        **channel_summary(channel),
    }


def channel_url(channel):
    # needed by peertube
    return {"url": ap_url(reverse("activitypub:channel", kwargs={"id": channel.id}))}


def channel_following(channel):
    return {}


def channel_followers(channel):
    return {}


def channel_playlists(channel):
    return {}


def channel_outbox(channel):
    return {}


def channel_inbox(channel):
    """Channel inbox definition is needed by peertube.

    This is a fake URL and is not intented to be reached."""

    channel_url = ap_url(reverse("activitypub:channel", kwargs={"id": channel.id}))
    inbox_url = f"{channel_url}/inbox"
    return {"inbox": inbox_url}


def channel_preferred_username(channel):
    """Channel preferred username is needed by peertube.

    it seems to not support spaces."""
    return {"preferredUsername": channel.slug}


def channel_name(channel):
    return {"name": channel.title}


def channel_endpoints(channel):
    channel_url = ap_url(reverse("activitypub:channel", kwargs={"id": channel.id}))
    inbox_url = f"{channel_url}/inbox"
    return {"endpoints": {"sharedInbox": inbox_url}}


def channel_public_key(channel):
    """Channel public key is needed by peertube.

    At the moment Pod only uses one key for AP so let's re-use it."""

    instance_actor_url = ap_url(reverse("activitypub:account"))
    return {
        "publicKey": {
            "id": f"{instance_actor_url}#main-key",
            "owner": instance_actor_url,
            "publicKeyPem": settings.ACTIVITYPUB_PUBLIC_KEY,
        }
    }


def channel_published(channel):
    """Pod does not have the information at moment."""
    return {}


def channel_icon(channel):
    return {}


def channel_support(channel):
    return {}


def channel_attributed_to(channel):
    """Channel attributions are needed by peertube."""
    return {
        "attributedTo": [
            {
                "type": "Person",
                "id": ap_url(
                    reverse("activitypub:account", kwargs={"username": owner.username})
                ),
            }
            for owner in channel.owners.all()
        ],
    }


def channel_image(channel):
    if channel.headband:
        return {
            "image": {
                "type": "Image",
                "url": channel.headband.file.url,
                "height": channel.headband.file.height,
                "width": channel.headband.file.width,
                "mediaType": channel.headband.file_type,
            }
        }
    return {}


def channel_summary(channel):
    if channel.description:
        return {
            "summary": channel.description,
        }
    return {}
