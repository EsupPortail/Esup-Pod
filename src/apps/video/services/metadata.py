import subprocess
import json
import math
from pathlib import Path  # noqa #F401


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
        print(f"Error extracting duration: {e}")
        return 0
