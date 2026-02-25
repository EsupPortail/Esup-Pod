import logging
import subprocess
import json
import math
from pathlib import Path  # noqa #F401
from datetime import date
from django.utils import timezone
from src.apps.video.services.core import ACCOMMODATION_YEARS, DEFAULT_YEAR_DATE_DELETE

logger = logging.getLogger(__name__)


def extract_video_duration(file_path):
    """
    Uses ffprobe to extract the duration in seconds of a video file.
    """
    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(file_path),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        duration_float = float(data["format"]["duration"])
        return math.ceil(duration_float)
    except FileNotFoundError:
        logger.warning(
            "ffprobe not found. Cannot extract duration from %s.",
            file_path,
        )
        return 0
    except subprocess.CalledProcessError as e:
        logger.warning(
            "ffprobe returned a non-zero exit code for %s: %s",
            file_path,
            e.stderr,
        )
        return 0
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(
            "Failed to parse ffprobe output for %s: %s",
            file_path,
            e,
            exc_info=True,
        )
        return 0


def calculate_expiration_date(owner):
    """
    Calculates the deletion date based on the user's affiliation.
    """
    user_affiliations = owner.owner.affiliation if hasattr(owner, 'owner') and hasattr(owner.owner, 'affiliation') else None
    if not user_affiliations:
        years = DEFAULT_YEAR_DATE_DELETE
    elif isinstance(user_affiliations, list):
        durations = [ACCOMMODATION_YEARS.get(aff, DEFAULT_YEAR_DATE_DELETE) for aff in user_affiliations]
        years = max(durations) if durations else DEFAULT_YEAR_DATE_DELETE
    else:
        years = ACCOMMODATION_YEARS.get(user_affiliations, DEFAULT_YEAR_DATE_DELETE)
    return date.today() + timezone.timedelta(days=years * 365)
