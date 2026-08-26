"""
Esup-Pod - Mediacad import service.
"""

import logging
import re
import requests
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def _extract_mediacad_id(source_url: str) -> str:
    """
    Extracts the Mediacad video ID from the source URL.
    Raises ValueError if the ID cannot be extracted.
    """
    match = re.search(r"/media/([a-zA-Z0-9_-]+)", source_url)
    if not match:
        raise ValueError(
            _("Cannot extract Mediacad video ID from URL: %(url)s") % {"url": source_url}
        )
    return match.group(1)


def _get_mediacad_base_url(source_url: str) -> str:
    """Extracts the base URL from a Mediacad URL."""
    match = re.match(r"(https?://[^/]+)", source_url)
    if not match:
        raise ValueError(_("Cannot extract base URL from: %(url)s") % {"url": source_url})
    return match.group(1)


def get_mediacad_metadata(source_url: str) -> dict:
    """
    Fetches metadata from a Mediacad video URL via its JSON API.
    Returns a dict with title, description, and download_url.
    Raises ValueError on failure.
    """
    try:
        video_id = _extract_mediacad_id(source_url)
        base_url = _get_mediacad_base_url(source_url)
        api_url = f"{base_url}/api/media/{video_id}"

        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        download_url = data.get("download_url") or data.get("url")
        if not download_url:
            raise ValueError(_("Cannot find download URL in Mediacad API response."))

        return {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "download_url": download_url,
        }

    except requests.exceptions.HTTPError as e:
        raise ValueError(
            _("HTTP error while fetching Mediacad metadata: %(error)s") % {"error": e}
        )
    except requests.exceptions.ConnectionError as e:
        raise ValueError(
            _("Connection error while fetching Mediacad metadata: %(error)s")
            % {"error": e}
        )
    except requests.exceptions.Timeout:
        raise ValueError(_("Mediacad API request timed out."))


def download_mediacad_video(source_url: str, dest_path: str) -> str:
    """
    Downloads a Mediacad video to the given destination path.
    Returns the destination path on success.
    Raises ValueError on failure.
    """
    from src.apps.import_video.services.downloader import download_file

    metadata = get_mediacad_metadata(source_url)
    return download_file(metadata["download_url"], dest_path)
