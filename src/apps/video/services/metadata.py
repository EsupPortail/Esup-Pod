import logging
import subprocess
import json
import math
from pathlib import Path  # noqa #F401

logger = logging.getLogger(__name__)


def extract_video_duration(file_path):
    """
    Utilise ffprobe pour extraire la durée en secondes d'un fichier vidéo.
    Retourne 0 si ffprobe n'est pas disponible ou si le fichier est invalide.
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
