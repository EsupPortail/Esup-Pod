"""
Esup-Pod - Generic video downloader service.
"""

import os
import logging
import requests

from django.utils.translation import gettext_lazy as _
from src.apps.import_video.conf import import_video_settings

logger = logging.getLogger(__name__)


def check_video_size(size_bytes: int) -> None:
    """
    Raises ValueError if the file size exceeds the allowed maximum.
    """
    max_bytes = import_video_settings.max_video_size_gb * 1024 * 1024 * 1024
    if max_bytes > 0 and size_bytes > max_bytes:
        raise ValueError(
            _(
                "File size (%(size).2f GB) exceeds the maximum allowed size (%(max).2f GB)."
            )
            % {
                "size": size_bytes / (1024**3),
                "max": import_video_settings.max_video_size_gb,
            }
        )


def download_file(url: str, dest_path: str) -> str:
    """
    Downloads a file from a URL to the given destination path.
    Returns the destination path on success.
    Raises ValueError on HTTP error or connection issue.
    """
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info("File downloaded successfully to %s", dest_path)
        return dest_path

    except requests.exceptions.HTTPError as e:
        raise ValueError(_("HTTP error while downloading file: %(error)s") % {"error": e})
    except requests.exceptions.ConnectionError as e:
        raise ValueError(
            _("Connection error while downloading file: %(error)s") % {"error": e}
        )
    except requests.exceptions.Timeout:
        raise ValueError(_("Download timed out."))
    except OSError as e:
        raise ValueError(
            _("File system error while saving download: %(error)s") % {"error": e}
        )
