"""
Esup-Pod - BigBlueButton import service.
"""

import logging
import re
import requests
from bs4 import BeautifulSoup
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def _extract_bbb_record_id(source_url: str) -> str:
    """
    Extracts the BBB recording ID from a playback URL.
    Raises ValueError if the ID cannot be extracted.
    """
    match = re.search(r"recordID=([a-zA-Z0-9_-]+)", source_url)
    if not match:
        raise ValueError(
            _("Cannot extract BBB recording ID from URL: %(url)s") % {"url": source_url}
        )
    return match.group(1)


def get_bbb_standard_metadata(source_url: str) -> dict:
    """
    Fetches metadata from a BBB standard recording playback page via HTML parsing.
    Returns a dict with title and download_url.
    Raises ValueError on failure.
    """
    try:
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.text.strip() if title_tag else "BBB Recording"

        video_tag = soup.find("video")
        if not video_tag:
            raise ValueError(_("No video element found in BBB playback page."))

        source_tag = video_tag.find("source")
        if not source_tag or not source_tag.get("src"):
            raise ValueError(_("No video source found in BBB playback page."))

        download_url = source_tag["src"]
        if not download_url.startswith("http"):
            base = re.match(r"(https?://[^/]+)", source_url)
            if base:
                download_url = base.group(1) + download_url

        return {
            "title": title,
            "download_url": download_url,
            "record_id": _extract_bbb_record_id(source_url),
        }

    except requests.exceptions.HTTPError as e:
        raise ValueError(
            _("HTTP error while fetching BBB recording page: %(error)s") % {"error": e}
        )
    except requests.exceptions.ConnectionError as e:
        raise ValueError(
            _("Connection error while fetching BBB recording page: %(error)s")
            % {"error": e}
        )
    except requests.exceptions.Timeout:
        raise ValueError(_("BBB recording page request timed out."))


def get_bbb_esr_metadata(source_url: str, meeting_api_url: str = None) -> dict:
    """
    Fetches metadata for a BBB ESR recording.
    Requires Meeting module integration for token generation.
    Raises NotImplementedError until Meeting module is migrated to V5.
    """
    raise NotImplementedError(
        _(
            "BBB ESR import requires the Meeting module which is not yet migrated to V5. "
            "This feature will be available once the Meeting module is integrated."
        )
    )


def download_bbb_video(source_url: str, dest_path: str) -> str:
    """
    Downloads a BBB standard recording to the given destination path.
    Returns the destination path on success.
    Raises ValueError on failure.
    """
    from src.apps.import_video.services.downloader import download_file

    metadata = get_bbb_standard_metadata(source_url)
    return download_file(metadata["download_url"], dest_path)
