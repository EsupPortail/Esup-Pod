"""Esup-Pod live HLS progression checks without downloading whole media segments."""

import time
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

MAX_PLAYLIST_BYTES = 1024 * 1024


def _read_hls(url: str, segment=False) -> bytes:
    """Read bounded HLS data without forwarding manager authentication."""
    URLValidator(schemes=["http", "https"])(url)
    headers = {"Cache-Control": "no-cache"}
    if segment:
        headers["Range"] = "bytes=0-1023"
    response = requests.get(
        url,
        headers=headers,
        timeout=getattr(settings, "ESUP_RUNNER_LIVE_HLS_TIMEOUT", (2, 2)),
        allow_redirects=False,
        stream=True,
    )
    try:
        if response.status_code not in ((200, 206) if segment else (200,)):
            raise ValueError("hls_http_error")
        data = bytearray()
        for chunk in response.iter_content(chunk_size=1024):
            data.extend(chunk)
            if len(data) > MAX_PLAYLIST_BYTES:
                raise ValueError("hls_playlist_too_large")
            if segment and data:
                break
        if not data:
            raise ValueError("hls_empty_response")
        return bytes(data)
    finally:
        response.close()


def _media_snapshot(url: str) -> dict:
    """Follow a master playlist and identify the latest media segment."""
    # Bound nested playlists and avoid loops in malformed HLS responses.
    for _ in range(3):
        lines = _read_hls(url).decode("utf-8-sig").splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        if not lines or lines[0] != "#EXTM3U":
            raise ValueError("invalid_hls_playlist")
        variants = [
            lines[index + 1]
            for index, line in enumerate(lines[:-1])
            if line.startswith("#EXT-X-STREAM-INF:")
            and not lines[index + 1].startswith("#")
        ]
        if variants:
            url = urljoin(url, variants[0])
            continue
        if "#EXT-X-ENDLIST" in lines:
            return {"ended": True}
        target = next(
            (
                line.split(":", 1)[1]
                for line in lines
                if line.startswith("#EXT-X-TARGETDURATION:")
            ),
            "0",
        )
        sequence = next(
            (
                line.split(":", 1)[1]
                for line in lines
                if line.startswith("#EXT-X-MEDIA-SEQUENCE:")
            ),
            "0",
        )
        segments = [line for line in lines if not line.startswith("#")]
        target, sequence = int(target), int(sequence)
        if target <= 0 or sequence < 0 or not segments:
            raise ValueError("invalid_hls_media_playlist")
        segment_url = urljoin(url, segments[-1])
        _read_hls(segment_url, segment=True)
        return {
            "ended": False,
            "playlist": url,
            "latest": (sequence + len(segments) - 1, segment_url),
            "target": target,
        }
    raise ValueError("nested_hls_playlists")


def probe_hls(url: str, key: str) -> str:
    """Confirm new accessible segments across probes, independently of the manager."""
    try:
        snapshot = _media_snapshot(url)
    except (requests.RequestException, ValidationError, ValueError, TypeError):
        return "unavailable"
    if snapshot["ended"]:
        cache.delete(key)
        return "ended"
    now = time.time()
    previous = cache.get(key)
    allowance = max(20, 3 * snapshot["target"])
    if (
        previous is None
        or previous["playlist"] != snapshot["playlist"]
        or snapshot["latest"][0] < previous["latest"][0]
        or now - previous["checked_at"] > allowance
    ):
        snapshot.update(observed_at=now, progressed_at=None)
    else:
        snapshot.update(
            observed_at=previous["observed_at"],
            progressed_at=(
                now
                if snapshot["latest"][0] > previous["latest"][0]
                else previous["progressed_at"]
            ),
        )
    snapshot["checked_at"] = now
    # This record outlives discovery caches; errors never refresh its progression.
    cache.set(key, snapshot, timeout=None)
    last_progress = snapshot["progressed_at"]
    if (
        now - (last_progress if last_progress is not None else snapshot["observed_at"])
        > allowance
    ):
        return "stalled"
    return "active" if last_progress is not None else "checking"
