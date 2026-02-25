import logging
import subprocess
import json
import math
from pathlib import Path  # noqa #F401

logger = logging.getLogger(__name__)


def extract_video_duration(file_path):
    """
    Utilise ffprobe pour extraire la durée en secondes d'un fichier vidéo.
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
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        duration_float = float(data["format"]["duration"])
        return math.ceil(duration_float)
    except Exception as e:
        logger.warning("Failed to extract duration from %s: %s", file_path, e)
        return 0

