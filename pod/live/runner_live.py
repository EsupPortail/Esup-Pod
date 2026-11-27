"""Esup-Pod automatic Live session discovery through the configured Runner manager."""

import hashlib
import logging
import time
from urllib.parse import quote, urlsplit

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .hls_probe import probe_hls

# As in the standard Esup-Pod configuration, CACHES['default'] must use Redis
# shared by all application processes and frontends to coordinate Live playback.
# HAProxy does not require session affinity for this mechanism. LocMemCache or
# independent Redis instances on each frontend do not share this state.

logger = logging.getLogger("pod.live")
# Technical grace period, deliberately independent of deployment settings.
FAILOVER_DELAY = 30
MANAGER_FAILURE_STATUSES = {500, 502, 503, 504}
LIVE_STATES = {
    "pending",
    "waiting_source",
    "starting",
    "running",
    "stopping",
    "completed",
    "failed",
}


class RunnerLiveError(ValueError):
    """Carry controlled diagnostics without manager responses or credentials."""

    def __init__(self, reason: str, stage: str, http_status=None):
        """Store the failure category, discovery step and optional HTTP status."""
        super().__init__(reason)
        self.reason = reason
        self.stage = stage
        self.http_status = http_status


def unavailable_stream(state: str = "unavailable", live_id=None) -> dict:
    """Return a public response with no playable URL."""
    return {"live_id": live_id, "state": state, "hls_ready": False, "hls_url": None}


def _live_payload(response, stage: str) -> dict:
    """Validate manager JSON without retaining remote error text in diagnostics."""
    try:
        payload = response.json()
    except ValueError:
        raise RunnerLiveError("invalid_json", stage, response.status_code) from None
    if not isinstance(payload, dict):
        raise RunnerLiveError("invalid_payload", stage, response.status_code)
    return payload


def _mediamtx_unavailable(response) -> bool:
    """Recognize Runner's explicit media-control outage without retaining its body."""
    if response.status_code != 503:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    return (
        isinstance(payload, dict)
        and payload.get("detail") == "MediaMTX control unavailable"
    )


def _get_json(manager, path: str, stage: str) -> dict:
    """Fetch Live JSON with server-side authentication and bounded HTTP timeouts."""
    try:
        response = requests.get(
            f"{manager.url.rstrip('/')}/live/{path}",
            headers={
                "Authorization": f"Bearer {manager.token}",
                "Accept": "application/json",
            },
            timeout=getattr(settings, "ESUP_RUNNER_LIVE_HTTP_TIMEOUT", (2, 4)),
            allow_redirects=False,
        )
    except requests.Timeout:
        raise RunnerLiveError("timeout", stage) from None
    except requests.exceptions.SSLError:
        raise RunnerLiveError("tls_error", stage) from None
    except requests.ConnectionError:
        raise RunnerLiveError("connection_error", stage) from None
    except requests.RequestException:
        raise RunnerLiveError("request_error", stage) from None
    if response.status_code != 200:
        if _mediamtx_unavailable(response):
            raise RunnerLiveError("mediamtx_unavailable", stage, response.status_code)
        raise RunnerLiveError("http_error", stage, response.status_code)
    return _live_payload(response, stage)


def _source_live_id(source: dict):
    """Extract a valid session identifier, or None when the source has no session."""
    if "live" not in source:
        raise RunnerLiveError("missing_live", "source")
    snapshot = source["live"]
    if snapshot is None:
        return None
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("live_id"), str):
        raise RunnerLiveError("invalid_live_session", "source")
    live_id = snapshot["live_id"]
    if not live_id:
        raise RunnerLiveError("missing_live_id", "source")
    return live_id


def _refresh_source(manager, source_id: str) -> tuple[dict, bool | None]:
    """Return refreshed playback and the current RTMP publication state.

    The publication state is None when the manager omits source readiness.
    Confirmed RTMP absence supersedes historical sessions and their HLS URLs.
    """
    source = _get_json(manager, f"sources/{quote(source_id, safe='')}", "source")
    publication_ready = source.get("source_ready")
    if not isinstance(publication_ready, bool):
        publication_ready = None
    live_id = _source_live_id(source)
    if live_id is None or publication_ready is False:
        # Current publication metrics supersede an old persisted session snapshot.
        return unavailable_stream("waiting_source", live_id), publication_ready
    # The source endpoint is a persisted snapshot. Never play it without refreshing.
    session = _get_json(manager, quote(live_id, safe=""), "session")
    if session.get("live_id") != live_id or session.get("source_id") != source_id:
        raise RunnerLiveError("session_mismatch", "session")
    state = session.get("state")
    if state not in LIVE_STATES:
        raise RunnerLiveError("invalid_state", "session")
    result = unavailable_stream(state, live_id)
    hls_url = session.get("hls_url")
    if state == "running" and session.get("hls_ready") is True and hls_url:
        try:
            URLValidator(schemes=["http", "https"])(hls_url)
        except (ValidationError, TypeError):
            raise RunnerLiveError("invalid_hls_url", "session") from None
        result.update(hls_ready=True, hls_url=hls_url)
    return result, publication_ready


def _log_stream_state(broadcaster, stream: dict, key: str):
    """Log availability changes and minute heartbeats without private media URLs."""
    scheme = urlsplit(stream["hls_url"]).scheme if stream["hls_url"] else None
    summary = (stream["state"], bool(stream["live_id"]), stream["hls_ready"], scheme)
    identity = repr((stream["live_id"], stream["hls_url"]))
    manager_id = cache.get(f"{key}:manager", broadcaster.runner_manager_id)
    signature = (manager_id, summary, hashlib.sha256(identity.encode()).hexdigest())
    state_key = f"{key}:state:{broadcaster.pk}"
    if cache.get(state_key) == signature:
        return
    logger.info(
        "Live availability for broadcaster %s "
        "(manager_id=%s, state=%s, session_present=%s, hls_ready=%s, hls_scheme=%s)",
        broadcaster.pk,
        manager_id,
        *summary,
    )
    cache.set(state_key, signature, timeout=60)


def log_playback_context(broadcaster, stream: dict, request):
    """Warn when a secure playback page receives an HTTP HLS media address."""
    if not broadcaster.is_runner_live or not request.is_secure():
        return
    if not stream["hls_url"] or urlsplit(stream["hls_url"]).scheme != "http":
        return
    identity = repr((broadcaster.pk, stream["hls_url"]))
    key = "runner-live:mixed-content:" + hashlib.sha256(identity.encode()).hexdigest()
    if not cache.add(key, True, timeout=60):
        return
    logger.warning(
        "Live playback unavailable for broadcaster %s "
        "(manager_id=%s, reason=mixed_content, page_scheme=https, hls_scheme=http)",
        broadcaster.pk,
        cache.get(f"{_stream_key(broadcaster)}:manager", broadcaster.runner_manager_id),
    )


def _discovery_failure(error: RunnerLiveError, key: str) -> dict:
    """Distinguish a temporary discovery failure from a confirmed absent stream."""
    network_error = error.reason in {"timeout", "connection_error"}
    temporary = (
        network_error
        or error.reason == "mediamtx_unavailable"
        or (
            error.reason == "http_error"
            and error.http_status in {429, 500, 502, 503, 504}
        )
    )
    result = unavailable_stream("manager_unavailable" if temporary else "unavailable")
    result.update(
        discovery_status="unreachable" if network_error else "error",
        retryable=temporary,
    )
    if not temporary:
        cache.delete_many([f"{key}:last-ready", f"{key}:hls"])
        return result
    previous = cache.get(f"{key}:last-ready")
    result["hls_status"] = "unavailable"
    if previous is None:
        return result
    result["live_id"] = previous["live_id"]
    result["hls_status"] = probe_hls(previous["hls_url"], f"{key}:hls")
    if result["hls_status"] == "active":
        result.update(previous)
    elif result["hls_status"] == "ended":
        result["state"] = "completed"
        cache.delete(f"{key}:last-ready")
    return result


def _remember_stream(result: dict, key: str):
    """Keep the latest confirmed URL until a confirmed stop or configuration error."""
    previous = cache.get(f"{key}:last-ready")
    if result["hls_ready"]:
        if previous != result:
            cache.delete(f"{key}:hls")
        cache.set(f"{key}:last-ready", result, timeout=None)
    else:
        cache.delete_many([f"{key}:last-ready", f"{key}:hls"])


def _discover_stream(broadcaster, manager):
    """Return playback, a controlled error and the RTMP publication state.

    Failures return no playback or publication state. Log only safe error
    categories; manager response bodies and credentials remain private.
    """
    try:
        result, publication_ready = _refresh_source(manager, broadcaster.source_id)
    except RunnerLiveError as caught:
        error = caught
    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
        ValidationError,
    ):
        # Exceptions can contain credentials/private URLs; keep diagnostics controlled.
        error = RunnerLiveError("invalid_response", "contract")
    else:
        return result, None, publication_ready
    logger.warning(
        "Live resolution unavailable for broadcaster %s "
        "(manager_id=%s, stage=%s, reason=%s, http_status=%s)",
        broadcaster.pk,
        manager.pk,
        error.stage,
        error.reason,
        error.http_status,
    )
    return None, error, None


def _manager_is_down(manager, error: RunnerLiveError) -> bool:
    """Confirm outages without confusing session failures with a dead manager."""
    network_error = error.reason in {"timeout", "connection_error"}
    if error.reason == "mediamtx_unavailable" or (
        network_error and error.stage == "source"
    ):
        return True
    if not network_error and not (
        error.reason == "http_error" and error.http_status in MANAGER_FAILURE_STATUSES
    ):
        return False
    # Generic health does not cover MediaMTX; its explicit outage is handled above.
    # Other session or Live endpoint failures alone do not establish downtime.
    # Match the current and legacy health endpoints used by the manager admin.
    for endpoint in ("api/health", "manager/health"):
        try:
            response = requests.get(
                f"{manager.url.rstrip('/')}/{endpoint}",
                headers={
                    "Authorization": f"Bearer {manager.token}",
                    "Accept": "application/json",
                },
                timeout=getattr(settings, "ESUP_RUNNER_LIVE_HTTP_TIMEOUT", (2, 4)),
                allow_redirects=False,
            )
        except requests.exceptions.SSLError:
            return False
        except (requests.Timeout, requests.ConnectionError):
            return True
        except requests.RequestException:
            return False
        if response.status_code != 404:
            return response.status_code in MANAGER_FAILURE_STATUSES
    return False


def _manager_identity(manager):
    """Fingerprint connection settings without placing credentials in cache keys."""
    return (manager.pk, manager.url, manager.token) if manager is not None else None


def _stream_key(broadcaster) -> str:
    """Isolate discovery, outage history and HLS by the complete manager pair."""
    identity = repr(
        (
            _manager_identity(broadcaster.runner_manager),
            _manager_identity(getattr(broadcaster, "secondary_runner_manager", None)),
            broadcaster.source_id,
        )
    )
    return "runner-live:" + hashlib.sha256(identity.encode()).hexdigest()


def _manager_enabled(manager) -> bool:
    """Require an explicitly enabled manager and server-side credentials."""
    return bool(manager and manager.is_active and manager.supports_live and manager.token)


def _forget_secondary(key: str):
    """Discard obsolete secondary continuity when primary playback wins or is revoked."""
    cache.delete_many(
        [f"{key}:outage", f"{key}:secondary:last-ready", f"{key}:secondary:hls"]
    )


def _failover_due(key: str) -> bool:
    """Require fresh failures spanning 30 seconds, shared across polling clients."""
    now = time.time()
    since = cache.get(f"{key}:outage", now)
    # An idle source must establish a new outage instead of reusing ancient failures.
    timeout = max(
        2 * FAILOVER_DELAY,
        2 * getattr(settings, "ESUP_RUNNER_LIVE_CACHE_TIMEOUT", 10),
    )
    cache.set(f"{key}:outage", since, timeout=timeout)
    return now - since >= FAILOVER_DELAY


def _secondary_stream(broadcaster, secondary, key: str) -> dict:
    """Resolve only the secondary, retaining its own independently verified HLS."""
    secondary_key = f"{key}:secondary"
    result, error, _ = _discover_stream(broadcaster, secondary)
    if error is not None:
        return _discovery_failure(error, secondary_key)
    _remember_stream(result, secondary_key)
    return result


def _usable_secondary(broadcaster):
    """Return only the explicitly enabled backup, distinct from the primary."""
    secondary = getattr(broadcaster, "secondary_runner_manager", None)
    if _manager_enabled(secondary) and secondary.pk != broadcaster.runner_manager_id:
        return secondary
    return None


def _select_secondary(broadcaster, secondary, key: str, primary=None, error=None) -> dict:
    """Select secondary media and keep checking for playable primary HLS.

    If secondary playback is unavailable, use the supplied primary result or
    discovery error to preserve independently active primary HLS when possible.
    """
    fallback = _secondary_stream(broadcaster, secondary, key)
    if not fallback["hls_ready"]:
        if error is not None:
            primary = _discovery_failure(error, key)
        if primary is not None and primary["hls_ready"]:
            return primary
    cache.set(f"{key}:manager", secondary.pk, timeout=None)
    # Use the shorter cadence until the primary has playable HLS again.
    return dict(fallback, retryable=True) if fallback["hls_ready"] else fallback


def _healthy_primary_stream(
    broadcaster, key, result, publication_ready, previous_manager
):
    """Use secondary media on confirmed absence and keep it through primary startup."""
    cache.delete(f"{key}:outage")
    _remember_stream(result, key)
    secondary = _usable_secondary(broadcaster)
    publication_absent = publication_ready is False or (
        publication_ready is None and result["live_id"] is None
    )
    if (
        not result["hls_ready"]
        and secondary is not None
        and (publication_absent or previous_manager == secondary.pk)
    ):
        return _select_secondary(broadcaster, secondary, key, primary=result)
    _forget_secondary(key)
    return result


def _resolve_stream(broadcaster, key: str) -> dict:
    """Prioritize ready primary HLS, with secondary playback on absence or outages."""
    manager = broadcaster.runner_manager
    if not manager.is_active:
        secondary = _usable_secondary(broadcaster)
        return (
            _select_secondary(broadcaster, secondary, key)
            if secondary is not None
            else unavailable_stream()
        )
    previous_manager = cache.get(f"{key}:manager", manager.pk)
    cache.set(f"{key}:manager", manager.pk, timeout=None)
    result, error, publication_ready = _discover_stream(broadcaster, manager)
    if error is None:
        return _healthy_primary_stream(
            broadcaster, key, result, publication_ready, previous_manager
        )
    secondary = _usable_secondary(broadcaster)
    if secondary is not None and (
        previous_manager == secondary.pk or _manager_is_down(manager, error)
    ):
        if previous_manager == secondary.pk or _failover_due(key):
            return _select_secondary(broadcaster, secondary, key, error=error)
    else:
        _forget_secondary(key)
    result = _discovery_failure(error, key)
    if previous_manager != manager.pk and not result["hls_ready"]:
        # A retryable response would leave the old secondary playing in the browser.
        result["retryable"] = False
    return result


def _invalidate_disabled_managers(broadcaster, key: str) -> bool:
    """Revoke disabled playback while preserving an eligible secondary's stream."""
    manager = broadcaster.runner_manager
    if not _manager_enabled(manager):
        secondary = _usable_secondary(broadcaster)
        if manager is not None and not manager.is_active and secondary is not None:
            cache.delete_many([f"{key}:outage", f"{key}:last-ready", f"{key}:hls"])
            if cache.get(f"{key}:manager") != secondary.pk:
                cache.delete(key)
            return True
        _forget_secondary(key)
        cache.delete_many([key, f"{key}:manager", f"{key}:last-ready", f"{key}:hls"])
        return False
    secondary = getattr(broadcaster, "secondary_runner_manager", None)
    if not _manager_enabled(secondary):
        _forget_secondary(key)
        if secondary and cache.get(f"{key}:manager") == secondary.pk:
            cache.delete(key)
    return True


def get_stream_info(broadcaster) -> dict:
    """Discover playback and tolerate manager outages while HLS remains active."""
    if not broadcaster.is_runner_live:
        return {
            "live_id": None,
            "state": "running" if broadcaster.status else "stopped",
            "hls_ready": bool(broadcaster.url),
            "hls_url": broadcaster.url or None,
        }
    if not broadcaster.runner_manager_id or not broadcaster.source_id:
        return unavailable_stream()
    key = _stream_key(broadcaster)
    if not _invalidate_disabled_managers(broadcaster, key):
        return unavailable_stream()
    cached = cache.get(key)
    if cached is not None:
        _log_stream_state(broadcaster, cached, key)
        return cached
    lock_key = f"{key}:refresh-lock"
    if not cache.add(lock_key, True, timeout=60):
        # Another request is resolving this same source, including its HLS probe.
        result = unavailable_stream("manager_unavailable")
        result.update(discovery_status="refreshing", retryable=True)
        return result
    try:
        # A previous owner may have filled the cache just before we got the lock.
        result = cache.get(key)
        if result is None:
            result = _resolve_stream(broadcaster, key)
            timeout = (
                getattr(settings, "ESUP_RUNNER_LIVE_READY_CACHE_TIMEOUT", 20)
                if result["hls_ready"] and not result.get("retryable")
                else getattr(settings, "ESUP_RUNNER_LIVE_CACHE_TIMEOUT", 10)
            )
            cache.set(key, result, timeout=timeout)
    finally:
        cache.delete(lock_key)
    _log_stream_state(broadcaster, result, key)
    return result
