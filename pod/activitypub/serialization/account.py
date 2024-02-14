from typing import Optional
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User

from pod.activitypub.constants import INSTANCE_ACTOR_ID
from pod.activitypub.utils import ap_url


def account_to_ap_actor(user: Optional[User]):
    """Serialize account to activitypub actor."""
    url_args = {"username": user.username} if user else {}
    response = {
        "id": ap_url(reverse("activitypub:account", kwargs=url_args)),
        **account_type(user),
        **account_url(user),
        **account_following(user),
        **account_followers(user),
        **account_inbox(user),
        **account_outbox(user),
        **account_endpoints(user),
        **account_public_key(user),
        **account_preferred_username(user),
        **account_name(user),
        **account_summary(user),
        **account_icon(user),
    }

    return response


def account_to_ap_group(user: Optional[User]):
    """Default channel for users.

    This is needed by Peertube, since in Peertube every
    Video must have at least one channel attached."""

    url_args = {"username": user.username} if user else {}

    # peertube needs a different username for the user account and the user channel
    # https://github.com/Chocobozzz/PeerTube/blob/5dfa07adb5ae8f1692a15b0f97ea0694894264c9/server/core/lib/activitypub/actors/shared/creator.ts#L89-L110
    preferred_username = (
        account_preferred_username(user)["preferredUsername"] + "_channel"
    )
    name = account_name(user)["name"] + "_channel"

    return {
        "type": "Group",
        "id": ap_url(reverse("activitypub:account_channel", kwargs=url_args)),
        "url": ap_url(reverse("activitypub:account_channel", kwargs=url_args)),
        **account_following(user),
        **account_followers(user),
        **account_playlists(user),
        **account_outbox(user),
        **account_inbox(user),
        **account_endpoints(user),
        **account_public_key(user),
        **account_icon(user),
        **account_summary(user),
        "preferredUsername": preferred_username,
        "name": name,
        "attributedTo": [
            {
                "type": "Person",
                "id": ap_url(reverse("activitypub:account", kwargs=url_args)),
            }
        ],
    }


def account_type(user: Optional[User]):
    return {"type": "Person" if user else "Application"}


def account_url(user: Optional[User]):
    url_args = {"username": user.username} if user else {}
    return {"url": ap_url(reverse("activitypub:account", kwargs=url_args))}


def account_following(user: Optional[User]):
    url_args = {"username": user.username} if user else {}
    return {"following": ap_url(reverse("activitypub:following", kwargs=url_args))}


def account_followers(user: Optional[User]):
    url_args = {"username": user.username} if user else {}
    return {"followers": ap_url(reverse("activitypub:followers", kwargs=url_args))}


def account_inbox(user: Optional[User]):
    url_args = {"username": user.username} if user else {}
    return {"inbox": ap_url(reverse("activitypub:inbox", kwargs=url_args))}


def account_outbox(user: Optional[User]):
    url_args = {"username": user.username} if user else {}
    return {"outbox": ap_url(reverse("activitypub:outbox", kwargs=url_args))}


def account_endpoints(user: Optional[User]):
    """sharedInbox is needed by peertube to send video updates."""
    url_args = {"username": user.username} if user else {}
    return {
        "endpoints": {
            "sharedInbox": ap_url(reverse("activitypub:inbox", kwargs=url_args))
        }
    }


def account_playlists(user: Optional[User]):
    return {}


def account_public_key(user: Optional[User]):
    instance_actor_url = ap_url(reverse("activitypub:account"))
    return {
        "publicKey": {
            "id": f"{instance_actor_url}#main-key",
            "owner": instance_actor_url,
            "publicKeyPem": settings.ACTIVITYPUB_PUBLIC_KEY,
        },
    }


def account_preferred_username(user: Optional[User]):
    return {"preferredUsername": user.username if user else INSTANCE_ACTOR_ID}


def account_name(user: Optional[User]):
    return {"name": user.username if user else INSTANCE_ACTOR_ID}


def account_summary(user: Optional[User]):
    if user:
        return {"summary": user.owner.commentaire}
    return {}


def account_icon(user: Optional[User]):
    if user and user.owner.userpicture:
        return {
            "icon": [
                {
                    "type": "Image",
                    "url": ap_url(user.owner.userpicture.file.url),
                    "height": user.owner.userpicture.file.width,
                    "width": user.owner.userpicture.file.height,
                    "mediaType": user.owner.userpicture.file_type,
                },
            ]
        }

    return {}
