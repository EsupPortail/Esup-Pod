"""
Esup-Pod - Generic video downloader service.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

MAX_VIDEO_SIZE_BYTES = 4 * 1024 * 1024 * 1024  # 4 GB default


def check_video_size(size_bytes: int) -> None:
    """
    Raises ValueError if the file size exceeds the allowed maximum.
    """
    if size_bytes > MAX_VIDEO_SIZE_BYTES:
        raise ValueError(
            f"File size ({size_bytes / (1024**3):.2f} GB) exceeds the maximum allowed size "
            f"({MAX_VIDEO_SIZE_BYTES / (1024**3):.2f} GB)."
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
        raise ValueError(f"HTTP error while downloading file: {e}")
    except requests.exceptions.ConnectionError as e:
        raise ValueError(f"Connection error while downloading file: {e}")
    except requests.exceptions.Timeout:
        raise ValueError("Download timed out.")
    except OSError as e:
        raise ValueError(f"File system error while saving download: {e}")
