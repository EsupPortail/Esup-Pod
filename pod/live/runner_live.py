"""Esup-Pod automatic Live session discovery through the configured Runner manager."""

import hashlib
import logging
from urllib.parse import quote, urlsplit

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .hls_probe import probe_hls

logger = logging.getLogger("pod.live")
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


def _refresh_source(manager, source_id: str) -> dict:
    """Discover the latest source session and refresh its HLS playback readiness."""
    source = _get_json(manager, f"sources/{quote(source_id, safe='')}", "source")
    live_id = _source_live_id(source)
    if live_id is None:
        return unavailable_stream("waiting_source")
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
    return result


def _log_stream_state(broadcaster, stream: dict, key: str):
    """Log availability changes and minute heartbeats without private media URLs."""
    scheme = urlsplit(stream["hls_url"]).scheme if stream["hls_url"] else None
    summary = (stream["state"], bool(stream["live_id"]), stream["hls_ready"], scheme)
    identity = repr((stream["live_id"], stream["hls_url"]))
    signature = (summary, hashlib.sha256(identity.encode()).hexdigest())
    state_key = f"{key}:state:{broadcaster.pk}"
    if cache.get(state_key) == signature:
        return
    logger.info(
        "Live availability for broadcaster %s "
        "(manager_id=%s, state=%s, session_present=%s, hls_ready=%s, hls_scheme=%s)",
        broadcaster.pk,
        broadcaster.runner_manager_id,
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
        broadcaster.runner_manager_id,
    )


def _discovery_failure(error: RunnerLiveError, key: str) -> dict:
    """Distinguish a temporary discovery failure from a confirmed absent stream."""
    network_error = error.reason in {"timeout", "connection_error"}
    temporary = network_error or (
        error.reason == "http_error" and error.http_status in {429, 500, 502, 503, 504}
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


def _resolve_stream(broadcaster, key: str) -> dict:
    """Resolve a source and record controlled manager failure diagnostics."""
    manager = broadcaster.runner_manager
    try:
        result = _refresh_source(manager, broadcaster.source_id)
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
        _remember_stream(result, key)
        return result
    logger.warning(
        "Live resolution unavailable for broadcaster %s "
        "(manager_id=%s, stage=%s, reason=%s, http_status=%s)",
        broadcaster.pk,
        manager.pk,
        error.stage,
        error.reason,
        error.http_status,
    )
    return _discovery_failure(error, key)


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
    manager = broadcaster.runner_manager
    # Include connection settings so manager/token edits invalidate cached results.
    identity = repr((manager.pk, manager.url, manager.token, broadcaster.source_id))
    key = "runner-live:" + hashlib.sha256(identity.encode()).hexdigest()
    if not manager.is_active or not manager.supports_live or not manager.token:
        cache.delete_many([key, f"{key}:last-ready", f"{key}:hls"])
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
