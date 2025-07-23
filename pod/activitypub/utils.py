import hashlib
import json
import logging
import random
import uuid
from collections import namedtuple
from urllib.parse import urlencode, urlunparse
from Crypto.PublicKey import RSA

import requests
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site

from pod.video.models import Video

from .constants import AP_REQUESTS_TIMEOUT, BASE_HEADERS
from .signature import (
    build_signature_payload,
    build_signature_headers,
    check_signature_payload,
    check_signature_headers,
)

logger = logging.getLogger(__name__)
URLComponents = namedtuple(
    typename="URLComponents",
    field_names=["scheme", "netloc", "url", "path", "query", "fragment"],
)


def make_url(
    scheme=None, netloc=None, params=None, path="", url="", fragment=""
) -> str:
    """Format activitypub url."""
    if scheme is None:
        scheme = "https" if getattr(settings, "SECURE_SSL_REDIRECT") else "http"

    if netloc is None:
        current_site = Site.objects.get_current()
        netloc = current_site.domain

    if params is not None:
        tuples = [(key, value) for key, values in params.items() for value in values]
        params = urlencode(tuples, safe=":")

    return urlunparse(
        URLComponents(
            scheme=scheme,
            netloc=netloc,
            query=params or {},
            url=url,
            path=path,
            fragment=fragment,
        )
    )


def ap_url(suffix="") -> str:
    """Returns a full absolute URL to be used in activitypub context."""
    return make_url(url=suffix)


def stable_uuid(seed, version=None):
    """Always returns the same UUID given the same input string."""

    full_seed = str(seed) + settings.SECRET_KEY
    m = hashlib.md5()
    m.update(full_seed.encode("utf-8"))
    return uuid.UUID(m.hexdigest(), version=version)


def make_magnet_url(video: Video, mp4):
    """Build a fake - but valid - magnet URL for compatibility with peertube < 6.2"""

    uuid = stable_uuid(video.id, version=4)
    fake_hash = "".join(
        random.choice("0123456789abcdefghijklmnopqrstuvwxyz") for _ in range(40)
    )
    payload = {
        "dn": [video.slug],
        "tr": [
            make_url(url="/tracker/announce"),
            make_url(scheme="ws", url="/tracker/announce"),
        ],
        "ws": [
            make_url(
                url=f"/static/streaming-playlists/hls/{uuid}-{mp4.height}-fragmented.mp4"
            )
        ],
        "xs": [make_url(url=f"/lazy-static/torrents/{uuid}-{mp4.height}-hls.torrent")],
        "xt": [f"urn:btih:{fake_hash}"],
    }
    return make_url(
        scheme="magnet",
        netloc="",
        params=payload,
    )


def ap_object(obj):
    """If obj is actually a link to a distant object, perform the request to get the object."""

    if isinstance(obj, str):
        result = requests.get(
            obj, headers=BASE_HEADERS, timeout=AP_REQUESTS_TIMEOUT
        ).json()
        logger.debug(
            "Read from AP endpoint: %s\n%s", obj, json.dumps(result, indent=True)
        )
        return result
    return obj


def ap_post(url, payload, **kwargs):
    """Sign and post an AP payload at a given URL."""

    logger.warning(
        "Posting to AP endpoint: %s\n%s", url, json.dumps(payload, indent=True)
    )

    private_key = RSA.import_key(settings.ACTIVITYPUB_PRIVATE_KEY)
    public_key_url = ap_url(reverse("activitypub:account")) + "#main-key"

    payload["signature"] = build_signature_payload(private_key, payload)
    signature_headers = build_signature_headers(
        private_key, public_key_url, payload, url
    )
    headers = kwargs.pop("headers", {})
    timeout = kwargs.pop("timeout", AP_REQUESTS_TIMEOUT)
    response = requests.post(
        url,
        json=payload,
        headers={**BASE_HEADERS, **signature_headers, **headers},
        timeout=timeout,
        **kwargs,
    )
    return response


def check_signatures(request):
    """Check the signatures from incoming requests."""

    # Reading the incoming request public key may
    # be slow due to the subsequent requests.
    # Some kind of caching might be useful here.

    payload = json.loads(request.body.decode())
    ap_actor = ap_object(payload["actor"])
    ap_pubkey = ap_object(ap_actor["publicKey"])
    ap_pubkey_pem = ap_pubkey["publicKeyPem"]
    public_key = RSA.import_key(ap_pubkey_pem)

    try:
        valid_payload = check_signature_payload(public_key, payload)
        valid_headers = check_signature_headers(
            public_key, payload, request.headers, request.get_raw_uri()
        )

    # abort if any header is missing
    except (KeyError, ValueError):
        return False

    return valid_payload and valid_headers
