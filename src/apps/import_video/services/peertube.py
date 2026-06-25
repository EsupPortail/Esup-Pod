"""
Esup-Pod - PeerTube import service.
"""

import logging
import re
import requests

logger = logging.getLogger(__name__)


def _extract_peertube_uuid(source_url: str) -> str:
    """
    Extracts the video UUID from a PeerTube URL.
    Supports /videos/watch/<uuid> and /w/<uuid> formats.
    Raises ValueError if UUID cannot be extracted.
    """
    patterns = [
        r"/videos/watch/([a-f0-9-]{36})",
        r"/w/([a-zA-Z0-9-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, source_url)
        if match:
            return match.group(1)
    raise ValueError(f"Cannot extract PeerTube video UUID from URL: {source_url}")


def _get_peertube_base_url(source_url: str) -> str:
    """Extracts the base URL (scheme + host) from a PeerTube URL."""
    match = re.match(r"(https?://[^/]+)", source_url)
    if not match:
        raise ValueError(f"Cannot extract base URL from: {source_url}")
    return match.group(1)


def get_peertube_metadata(source_url: str) -> dict:
    """
    Fetches metadata from a PeerTube video URL via the PeerTube REST API.
    Returns a dict with title, description, published_at, and download_url.
    Raises ValueError on failure.
    """
    try:
        uuid = _extract_peertube_uuid(source_url)
        base_url = _get_peertube_base_url(source_url)
        api_url = f"{base_url}/api/v1/videos/{uuid}"

        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        files = data.get("files", [])
        if not files:
            streaming_playlists = data.get("streamingPlaylists", [])
            if streaming_playlists:
                files = streaming_playlists[0].get("files", [])

        if not files:
            raise ValueError("No downloadable files found for this PeerTube video.")

        download_url = files[0].get("fileDownloadUrl") or files[0].get("fileUrl")
        if not download_url:
            raise ValueError("Cannot find download URL in PeerTube API response.")

        return {
            "title": data.get("name", ""),
            "description": data.get("description", ""),
            "published_at": data.get("publishedAt"),
            "download_url": download_url,
            "uuid": uuid,
        }

    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error while fetching PeerTube metadata: {e}")
    except requests.exceptions.ConnectionError as e:
        raise ValueError(f"Connection error while fetching PeerTube metadata: {e}")
    except requests.exceptions.Timeout:
        raise ValueError("PeerTube API request timed out.")


def download_peertube_video(source_url: str, dest_path: str) -> str:
    """
    Downloads a PeerTube video to the given destination path.
    Returns the destination path on success.
    Raises ValueError on failure.
    """
    from src.apps.import_video.services.downloader import download_file

    metadata = get_peertube_metadata(source_url)
    return download_file(metadata["download_url"], dest_path)
