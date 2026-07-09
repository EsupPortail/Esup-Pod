"""
Esup-Pod - YouTube import service.
"""

import logging
import os
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def get_youtube_metadata(source_url: str) -> dict:
    """
    Fetches metadata from a YouTube video URL using yt-dlp.
    Returns a dict with title, publish_date and filesize.
    Raises ValueError on failure.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ValueError(_("yt-dlp is not installed. Cannot import YouTube videos."))

    ydl_opts = {"quiet": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source_url, download=False)
            return {
                "title": info.get("title", ""),
                "publish_date": info.get("upload_date"),
                "filesize": info.get("filesize") or info.get("filesize_approx", 0),
            }
    except Exception as e:
        raise ValueError(_("Failed to fetch YouTube metadata: %(error)s") % {"error": e})


def download_youtube_video(source_url: str, dest_dir: str) -> str:
    """
    Downloads a YouTube video using yt-dlp.
    Returns the path of the downloaded file.
    Raises ValueError on failure.
    """
    try:
        import yt_dlp
    except ImportError:
        raise ValueError(_("yt-dlp is not installed. Cannot import YouTube videos."))

    from src.apps.import_video.services.downloader import check_video_size

    metadata = get_youtube_metadata(source_url)
    check_video_size(metadata["filesize"])

    os.makedirs(dest_dir, exist_ok=True)
    ydl_opts = {
        "outtmpl": os.path.join(dest_dir, "%(id)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "quiet": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(source_url, download=True)
            filename = ydl.prepare_filename(info)
            logger.info("YouTube video downloaded to %s", filename)
            return filename
    except Exception as e:
        raise ValueError(_("Failed to download YouTube video: %(error)s") % {"error": e})
